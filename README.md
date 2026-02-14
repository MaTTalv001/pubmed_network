# PubMed 共著ネットワーク可視化

特定の著者名を入力し、PubMed の論文データからその著者を起点とした共著関係のネットワークを可視化・分析する Streamlit アプリです。

## 機能

- **共著ネットワーク可視化** — Pyvis によるインタラクティブなネットワーク図（ドラッグ・ホバー対応）
- **ネットワーク分析指標** — 次数中心性・媒介中心性・近接中心性・クラスタリング係数
- **コミュニティ検出** — 貪欲モジュラリティ法による研究グループの自動検出・色分け表示
- **論文一覧** — 取得した論文の詳細と PubMed へのリンク

## セットアップ

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 起動

```bash
streamlit run app.py
```

## ファイル構成

```
pubmed-network/
├── app.py                        # Streamlit メインアプリ（UI）
├── requirements.txt              # 依存パッケージ
└── pubmed_network/               # コアロジック
    ├── __init__.py
    ├── pubmed_client.py          # NCBI E-utilities API クライアント
    ├── network_builder.py        # NetworkX によるグラフ構築・分析
    └── visualizer.py             # Pyvis によるネットワーク可視化
```

## 使い方

1. 著者名を入力（例: `Yamanaka S`）
2. 最大取得論文数・最小共著数フィルターを調整
3. 「検索」ボタンをクリック
4. ネットワーク図・分析指標・コミュニティ・論文一覧が表示される

## 技術スタック

| ライブラリ | 用途 |
|---|---|
| Streamlit | Web UI |
| Requests | PubMed API 通信 |
| NetworkX | グラフ構築・中心性分析・コミュニティ検出 |
| Pyvis | インタラクティブネットワーク可視化 |
| Pandas | データ表示 |

## API について

- NCBI E-utilities API を使用（APIキー不要）
- NCBI への負荷軽減のため、リクエストレートを低めに設定しています
- 同一ネットワークからの同時アクセスが多い場合、NCBI 側でレート制限が適用される可能性があります

## 注意事項

- 著者名の表記揺れにより、同一著者が別ノードとして表示される場合があります
- 研究支援を目的としたツールであり、分析結果の正確性を保証するものではありません
