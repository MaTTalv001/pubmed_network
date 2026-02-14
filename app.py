import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from pubmed_network import search_pubmed, fetch_articles
from pubmed_network import build_coauthor_network, detect_communities, compute_centralities, get_network_stats
from pubmed_network import generate_network_html

st.title("PubMed 共著ネットワーク可視化")
st.caption("特定の著者名を入力し、その著者を起点とした共著関係のネットワークを可視化・分析するツールです。")

# --- 注意事項（トップに配置・折りたたみ） ---
with st.expander("注意事項（必ずお読みください）"):
    st.markdown("""
**PubMed API (NCBI E-utilities) の利用制限**

- 本アプリは NCBI E-utilities API を使用しています。NCBIへの負荷を軽減する目的で接続レートは低めに設定しています。
- そのため、大量の論文を取得する場合、データ取得に時間がかかることがあります。
- NCBI の利用規約により、過度なリクエストはIPアドレス単位でブロックされる可能性があります。

**社内利用時の注意**

- 同一ネットワークから多数のユーザーが同時にアクセスした場合、NCBI 側でレート制限が適用される可能性があります。
- 頻繁な検索を避け、必要な範囲で利用してください。
- 取得論文数が多いほどネットワーク構築・可視化の処理負荷が増大します。初回は少ない件数（30件程度）から試すことを推奨します。

**免責事項**

- 本アプリは研究支援を目的としたツールであり、分析結果の正確性を保証するものではありません。
- PubMed のデータは著者名の表記揺れを含む場合があり、同一著者が別ノードとして表示されることがあります。
""")

# --- 検索フォーム（メインエリア） ---
col_query, col_max, col_min, col_btn = st.columns([3, 2, 2, 1])
with col_query:
    query = st.text_input("著者名", placeholder="例: Kitanishi Y")
with col_max:
    max_results = st.slider("最大取得論文数", 10, 200, 30, step=10)
with col_min:
    min_coauthor = st.slider("最小共著数フィルター", 1, 10, 1)
with col_btn:
    st.write("")  # spacer for alignment
    search_clicked = st.button("検索", type="primary", use_container_width=True)

st.divider()

# --- 検索実行・結果表示 ---
if search_clicked and query:
    # PubMed の Author フィールドに限定して検索
    search_query = f"{query}[Author]"

    with st.spinner("PubMed を検索中..."):
        pmids = search_pubmed(search_query, max_results)

    if not pmids:
        st.warning("論文が見つかりませんでした。著者名を確認してください（例: Yamanaka S）。")
        st.stop()

    st.info(f"{len(pmids)} 件の論文が見つかりました。詳細を取得中...")

    with st.spinner("論文データを取得中..."):
        articles = fetch_articles(pmids)

    if not articles:
        st.warning("著者データを含む論文が見つかりませんでした。")
        st.stop()

    with st.spinner("ネットワークを構築中..."):
        G = build_coauthor_network(articles)
        communities = detect_communities(G)
        centralities = compute_centralities(G)
        stats = get_network_stats(G)

    # ネットワーク統計
    st.subheader("ネットワーク統計")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("著者数", stats.get("nodes", 0))
    col2.metric("共著関係数", stats.get("edges", 0))
    col3.metric("密度", stats.get("density", 0))
    col4.metric("連結成分数", stats.get("connected_components", 0))
    col5.metric("最大成分サイズ", stats.get("largest_component_size", 0))
    col6.metric("平均クラスタリング係数", stats.get("avg_clustering", 0))

    # ネットワーク可視化
    st.subheader("共著ネットワーク")
    html = generate_network_html(G, communities, min_coauthor=min_coauthor, height="650px")
    components.html(html, height=700, scrolling=True)

    # 中心性指標テーブル
    st.subheader("著者別 中心性指標")
    if centralities:
        df = pd.DataFrame.from_dict(centralities, orient="index")
        df.index.name = "著者"
        df = df.rename(columns={
            "paper_count": "論文数",
            "affiliation": "所属",
            "degree_centrality": "次数中心性",
            "betweenness_centrality": "媒介中心性",
            "closeness_centrality": "近接中心性",
            "clustering_coefficient": "クラスタリング係数",
        })
        df = df.sort_values("次数中心性", ascending=False)
        st.dataframe(df, use_container_width=True, height=400)

    # コミュニティ情報
    st.subheader("コミュニティ一覧")
    if communities:
        comm_groups: dict[int, list[str]] = {}
        for node, cid in communities.items():
            comm_groups.setdefault(cid, []).append(node)
        for cid in sorted(comm_groups.keys()):
            members = comm_groups[cid]
            with st.expander(f"コミュニティ {cid}（{len(members)} 名）"):
                st.write(", ".join(sorted(members)))

    st.divider()

    # --- 指標・グラフの見方（折りたたみ） ---
    with st.expander("ネットワーク図・指標の見方"):
        st.markdown("""
**ネットワーク図の読み方**

- **ノード（丸）** = 著者。サイズが大きいほど論文数が多い著者です。
- **エッジ（線）** = 共著関係。線が太いほど共著論文数が多いことを示します。
- **色** = コミュニティ（研究グループ）。同じ色の著者は互いに密に共著し合う傾向があります。
- ノードをドラッグして配置を調整したり、ホバーで著者情報を確認できます。

**ネットワーク統計の意味**

| 指標 | 意味 |
|---|---|
| 著者数 | ネットワークに含まれる著者の総数 |
| 共著関係数 | 著者ペア間の共著関係の総数 |
| 密度 | 理論上ありうる全共著関係のうち、実際に存在する割合（0〜1）。高いほど著者同士の繋がりが密 |
| 連結成分数 | 互いに到達可能な著者グループの数。1なら全員が繋がっている |
| 最大成分サイズ | 最も大きい連結グループに含まれる著者数 |
| 平均クラスタリング係数 | 著者の共著者同士がどれだけ互いに共著しているかの平均（0〜1） |

**著者別 中心性指標の意味**

| 指標 | 意味 | 高い著者の特徴 |
|---|---|---|
| 次数中心性 | 共著者の多さ（全著者数に対する割合） | 多くの研究者と共同研究している |
| 媒介中心性 | 他の著者ペアを繋ぐ最短経路上にどれだけ位置するか | 異なる研究グループ間の「橋渡し役」 |
| 近接中心性 | ネットワーク内の全著者への平均的な近さ | ネットワーク全体の中心にいる |
| クラスタリング係数 | 自分の共著者同士がどれだけ互いに共著しているか | 緊密な研究チームに属している |

**コミュニティとは**

共著関係の密度に基づいて自動検出された研究グループです。同一コミュニティ内の著者は、異なるコミュニティの著者よりも互いに共著する頻度が高い傾向にあります。
""")

    # --- 指標の計算式（折りたたみ） ---
    with st.expander("指標の計算式（数学的定義）"):
        st.markdown("グラフ $G = (V, E)$ において、ノード数 $n = |V|$ とします。")

        st.markdown("---")
        st.markdown("**密度 (Density)**")
        st.markdown("実在するエッジ数 $|E|$ と、理論上の最大エッジ数の比：")
        st.latex(r"\rho = \frac{2|E|}{n(n-1)}")

        st.markdown("---")
        st.markdown("**次数中心性 (Degree Centrality)**")
        st.markdown("ノード $v$ の次数 $\\deg(v)$（隣接ノード数）を最大可能次数で正規化：")
        st.latex(r"C_D(v) = \frac{\deg(v)}{n - 1}")

        st.markdown("---")
        st.markdown("**媒介中心性 (Betweenness Centrality)**")
        st.markdown("全ノードペア $(s, t)$ の最短経路のうち、ノード $v$ を通過する割合：")
        st.latex(r"C_B(v) = \sum_{s \neq v \neq t \in V} \frac{\sigma_{st}(v)}{\sigma_{st}}")
        st.markdown("$\\sigma_{st}$：$s$ から $t$ への最短経路の総数、$\\sigma_{st}(v)$：そのうち $v$ を経由するものの数")

        st.markdown("---")
        st.markdown("**近接中心性 (Closeness Centrality)**")
        st.markdown("ノード $v$ から他の全ノードへの最短距離の平均の逆数：")
        st.latex(r"C_C(v) = \frac{n - 1}{\sum_{u \neq v} d(v, u)}")
        st.markdown("$d(v, u)$：ノード $v$ から $u$ への最短経路長")

        st.markdown("---")
        st.markdown("**クラスタリング係数 (Clustering Coefficient)**")
        st.markdown("ノード $v$ の隣接ノード間に実際に存在するエッジ数と、最大可能数の比：")
        st.latex(r"C_{cluster}(v) = \frac{2 \cdot |\{e_{jk} : v_j, v_k \in N(v),\; e_{jk} \in E\}|}{\deg(v)(\deg(v) - 1)}")
        st.markdown("$N(v)$：ノード $v$ の隣接ノード集合")

        st.markdown("---")
        st.markdown("**平均クラスタリング係数**")
        st.latex(r"\bar{C} = \frac{1}{n} \sum_{v \in V} C_{cluster}(v)")

    # --- 論文リスト（最下部・折りたたみ） ---
    st.markdown("---")
    st.subheader("取得論文一覧")
    for art in articles:
        year = f" ({art['year']})" if art.get("year") else ""
        authors_str = ", ".join(
            f"{a['last_name']} {a['first_name'][0]}" if a.get("first_name") else a["last_name"]
            for a in art["authors"]
        )
        pmid = art.get("pmid", "")
        link = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
        with st.expander(f"{art.get('title', 'No title')}{year}"):
            st.markdown(f"**著者:** {authors_str}")
            if art.get("journal"):
                st.markdown(f"**雑誌:** {art['journal']}")
            if link:
                st.markdown(f"**PubMed:** [{pmid}]({link})")

elif search_clicked:
    st.warning("著者名を入力してください。")
