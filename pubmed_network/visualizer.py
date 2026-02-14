import math

from pyvis.network import Network

COMMUNITY_COLORS = [
    "#e6194b", "#3cb44b", "#4363d8", "#f58231", "#911eb4",
    "#42d4f4", "#f032e6", "#bfef45", "#fabed4", "#469990",
    "#dcbeff", "#9A6324", "#800000", "#aaffc3", "#808000",
    "#000075", "#a9a9a9",
]


def generate_network_html(
    G,
    communities: dict,
    min_coauthor: int = 1,
    height: str = "600px",
) -> str:
    """Generate an interactive Pyvis HTML string for the co-author network."""
    net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="#333333")
    net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=100)

    filtered_edges = [
        (u, v) for u, v, d in G.edges(data=True) if d.get("weight", 1) >= min_coauthor
    ]
    nodes_in_filtered = set()
    for u, v in filtered_edges:
        nodes_in_filtered.add(u)
        nodes_in_filtered.add(v)

    if not nodes_in_filtered:
        return "<p>No nodes to display with the current filter.</p>"

    max_papers = max(
        (G.nodes[n].get("paper_count", 1) for n in nodes_in_filtered), default=1
    )

    for node in nodes_in_filtered:
        paper_count = G.nodes[node].get("paper_count", 1)
        affiliation = G.nodes[node].get("affiliation", "")
        comm_id = communities.get(node, 0)
        color = COMMUNITY_COLORS[comm_id % len(COMMUNITY_COLORS)]
        size = 10 + 30 * math.sqrt(paper_count / max_papers)
        title = f"<b>{node}</b><br>Papers: {paper_count}<br>Community: {comm_id}"
        if affiliation:
            title += f"<br>Affiliation: {affiliation[:100]}"
        net.add_node(node, label=node, size=size, color=color, title=title)

    max_weight = max(
        (G[u][v].get("weight", 1) for u, v in filtered_edges), default=1
    )

    for u, v in filtered_edges:
        weight = G[u][v].get("weight", 1)
        width = 1 + 4 * (weight / max_weight)
        net.add_edge(u, v, value=weight, width=width, title=f"Co-authored: {weight}")

    net.set_options("""
    {
      "interaction": {
        "hover": true,
        "tooltipDelay": 100,
        "navigationButtons": true
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -3000,
          "centralGravity": 0.3,
          "springLength": 100,
          "damping": 0.09
        },
        "stabilization": {
          "iterations": 150
        }
      }
    }
    """)

    return net.generate_html()
