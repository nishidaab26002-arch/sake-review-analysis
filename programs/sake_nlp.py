"""日本酒口コミ分析：前処理の共通モジュール（マスキング + Sudachi分かち書き）

04_preprocess（学習データ作成）と 06_analysis（新規銘柄の推論）の両方で
**まったく同じ前処理** を使うため、関数をここに集約している。
"""
import re

# ---------------------------------------------------------------- Sudachi（初回利用時に初期化）
_sudachi = None
_MODE = None


def _get_sudachi():
    global _sudachi, _MODE
    if _sudachi is None:
        from sudachipy import dictionary, tokenizer
        _sudachi = dictionary.Dictionary(dict="full").create()
        _MODE = tokenizer.Tokenizer.SplitMode.C
    return _sudachi, _MODE


# ---------------------------------------------------------------- 辞書類
# 日本酒用語は Sudachi が細かく分割してしまうため、表層形ベースで再結合する
SAKE_COMPOUNDS = {
    ('無', '濾過'): '無濾過',
    ('生', '原酒'): '生原酒',
    ('生', '原', '酒'): '生原酒',
    ('生原', '酒'): '生原酒',
    ('山', '廃'): '山廃',
    ('生', '酛'): '生酛',
    ('速', '醸'): '速醸',
    ('火', '入れ'): '火入れ',
    ('荒', '走り'): '荒走り',
    ('中', '取り'): '中取り',
    ('無', '加水'): '無加水',
    ('袋', '吊り'): '袋吊り',
}

# Sudachi の正規化形の表記ゆれ補正
NORMALIZATION_FIX = {'旨み': '旨味', '円やか': 'まろやか'}

# 味わいマップの純粋性を高めるため除外する語（正規化後の形）
SAKE_STOP_WORDS = {
    # 頻出の一般動詞
    "為る", "有る", "居る", "成る", "言う", "思う", "来る", "行く", "見る", "含む",
    "よう", "こと", "此れ", "此の", "無い", "感じ", "感じる", "其れ", "其の",
    # 行動・メタ単語
    "飲む", "購入", "開栓", "頂く", "日本酒", "酒造", "香り", "味わい",
    # 感情・主観評価
    "良い", "美味しい", "旨い",
    # スペック・特定ジャンル
    "純米吟醸", "生原酒", "純米酒", "純米", "精米歩合", "無濾過", "山田錦", "特別純米",
}

STOP_POS = {'助詞', '助動詞', '記号', '補助記号', '接続詞', '感動詞', '接尾辞', '接頭辞'}

# マスキング対象（地方バイアスを誘発しうる語）
PREFECTURE_NAMES = [
    '北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島',
    '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川',
    '新潟', '富山', '石川', '福井', '山梨', '長野', '岐阜', '静岡', '愛知',
    '三重', '滋賀', '京都', '大阪', '兵庫', '奈良', '和歌山',
    '鳥取', '島根', '岡山', '広島', '山口',
    '徳島', '香川', '愛媛', '高知',
    '福岡', '佐賀', '長崎', '熊本', '大分', '宮崎', '鹿児島', '沖縄',
]
REGION_NAMES = ['東北', '関東', '中部', '北陸', '関西', '近畿', '中国地方', '四国', '九州']
GEO_NAMES = PREFECTURE_NAMES + REGION_NAMES

STEREOTYPE_PHRASES = [
    '東北らしい', '新潟らしい', '秋田らしい', '山形らしい', '福島らしい',
    '北海道らしい', '岩手らしい', '青森らしい',
    '灘の酒', '灘の', '灘', '伏見の酒', '伏見の', '伏見',
    '関西らしい', '京都らしい', '兵庫らしい', '奈良らしい', '女酒', '男酒',
    '広島らしい', '西条の',
    '四国らしい', '高知らしい', '土佐の',
    '九州らしい', '南国', '福岡らしい', '佐賀らしい',
    '信州らしい', '長野らしい', '静岡らしい',
    '地酒らしい', '地元の',
]

_MASK_TERMS = sorted(STEREOTYPE_PHRASES, key=len, reverse=True)
_GEO_TERMS = sorted(GEO_NAMES, key=len, reverse=True)
_RASHII = re.compile(r'[ぁ-ゟァ-ヶ一-鿿]{2,5}らしい')
_NUMERIC = re.compile(r'[\d\.\,\%\+\-\s]+')


# ---------------------------------------------------------------- 前処理関数
def mask_review(text):
    """口コミ本文から地名・紋切り型表現（〇〇らしい 等）を除去する"""
    for phrase in _MASK_TERMS:
        text = text.replace(phrase, '')
    for name in _GEO_TERMS:
        text = text.replace(name, '')
    text = _RASHII.sub('', text)
    return re.sub(r'\s+', ' ', text).strip()


def _merge_compounds(tokens):
    """表層形が SAKE_COMPOUNDS に一致する連続形態素を1語にまとめる（フィルタ前に実施）"""
    surfaces = [t['surface'] for t in tokens]
    merged, i = [], 0
    while i < len(tokens):
        for length in (3, 2):
            key = tuple(surfaces[i:i + length])
            if len(key) == length and key in SAKE_COMPOUNDS:
                word = SAKE_COMPOUNDS[key]
                merged.append({'surface': word, 'normalized': word, 'pos': '名詞'})
                i += length
                break
        else:
            merged.append(tokens[i])
            i += 1
    return merged


def tokenize(text):
    """Sudachi(SplitMode.C) で分かち書きし、正規化形のトークン列を返す

    1. 形態素解析  2. 日本酒用語の再結合  3. 品詞フィルタ・表記ゆれ補正・
    数値除外・ストップワード除外・2文字以上のみ採用
    """
    sudachi, mode = _get_sudachi()
    try:
        tokens = [{'surface': m.surface(), 'normalized': m.normalized_form(),
                   'pos': m.part_of_speech()[0]} for m in sudachi.tokenize(text, mode)]
    except Exception:
        return []

    result = []
    for t in _merge_compounds(tokens):
        if t['pos'] in STOP_POS:
            continue
        word = NORMALIZATION_FIX.get(t['normalized'], t['normalized'])
        if _NUMERIC.fullmatch(word) or word in SAKE_STOP_WORDS or len(word) < 2:
            continue
        result.append(word)
    return result


def normalize_word(word):
    """キーワード1語を、学習時と同じSudachi正規化形に変換する（味わい辞書用）"""
    sudachi, mode = _get_sudachi()
    return ''.join(m.normalized_form() for m in sudachi.tokenize(word, mode))


# ---------------------------------------------------------------- データ入出力
def load_tokenized(path):
    """04_preprocess が出力した CSV を読み込み、tokens 列を list[str] にして返す"""
    import pandas as pd
    df = pd.read_csv(path, encoding='utf-8-sig')
    df['tokens'] = df['tokens'].str.split(' ')
    return df


def to_tagged_docs(df):
    """口コミ1件 = 1ドキュメント、タグは銘柄（都道府県_銘柄_蔵元）の TaggedDocument のリスト"""
    from gensim.models.doc2vec import TaggedDocument
    return [TaggedDocument(words=row.tokens, tags=[row.tag]) for row in df.itertuples()]
