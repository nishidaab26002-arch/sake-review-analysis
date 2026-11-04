# 日本酒の口コミ分析

日本酒の口コミから、銘柄ごとの味わいをDoc2Vecで数値化し、可視化する分析プロジェクトです。
スクレイピング・前処理・機械学習・分析/可視化をPython/Google Colabで実装しました。
分析の背景・結果・考察に関してはポートフォリオ資料としてPDFにまとめています。
このリポジトリにはコードのみを置き、口コミデータ・学習済みモデルは含みません。

## 処理の流れ

| # | ノートブック | 内容 |
|---|---|---|
| 01 | `01_scrape_reviews.ipynb` | Playwright + BeautifulSoup で口コミを収集 |
| 02 | `02_scrape_maker_address_and_water_hardness.ipynb` | 蔵元の所在地と水道水の硬度を収集 |
| 03 | `03_parse_review_text.ipynb` | 口コミ文字列を項目ごとに分解 |
| 04 | `04_preprocess_tokenize.ipynb` | 地名のマスキング + Sudachi による分かち書き |
| 05 | `05_train_doc2vec.ipynb` | Doc2Vec で銘柄ベクトルを学習 |
| 06 | `06_analysis_visualization.ipynb` | k-means・PCA による味わいマップ、レーダーチャート、水の硬度の検証 |

## 使用技術

Python / Playwright / BeautifulSoup / pandas / Sudachi / gensim (Doc2Vec) / scikit-learn / matplotlib

## 実行方法（Google Colab）

1. `sake_nlp.py` を Google Drive の作業フォルダに置く。
2. 各ノートブックの設定セルで `BASE_DIR` を自分の Drive のパスに変更する。
3. 01 → 06 の順に実行する。

## 注意事項

- 口コミは [SAKETIME](https://www.saketime.jp/) から、サーバーに負荷をかけないよう間隔を空けて、個人の学習・分析目的で取得しました。
- 口コミの本文・取得したデータは公開していません。
- 本リポジトリは個人のポートフォリオです。
