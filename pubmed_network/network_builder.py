from itertools import combinations

import networkx as nx
from networkx.algorithms import community as nx_community


def _author_key(author: dict) -> str:
    """Create a canonical author name key: 'Last FM'."""
    last = author["last_name"]
    first = author["first_name"]
    if first:
        initials = "".join(part[0] for part in first.split() if part)
        return f"{last} {initials}"
    return last


def build_coauthor_network(articles: list[dict]) -> nx.Graph:
    """Build a co-author network graph from article data."""
    G = nx.Graph()

    for article in articles:
        authors = article["authors"]
        author_keys = []
        for a in authors:
            key = _author_key(a)
            author_keys.append(key)
            if not G.has_node(key):
                G.add_node(key, paper_count=0, affiliation=a["affiliation"])
            G.nodes[key]["paper_count"] = G.nodes[key].get("paper_count", 0) + 1
            if a["affiliation"] and not G.nodes[key].get("affiliation"):
                G.nodes[key]["affiliation"] = a["affiliation"]

        for a1, a2 in combinations(author_keys, 2):
            if G.has_edge(a1, a2):
                G[a1][a2]["weight"] += 1
            else:
                G.add_edge(a1, a2, weight=1)

    return G


def detect_communities(G: nx.Graph) -> dict:
    """Detect communities using greedy modularity. Returns {node: community_id}."""
    if len(G.nodes) == 0:
        return {}
    undirected = G.copy()
    components = list(nx.connected_components(undirected))
    community_map = {}
    community_id = 0
    for comp in components:
        subgraph = undirected.subgraph(comp)
        if len(comp) < 3:
            for node in comp:
                community_map[node] = community_id
            community_id += 1
        else:
            try:
                comms = nx_community.greedy_modularity_communities(subgraph)
                for comm in comms:
                    for node in comm:
                        community_map[node] = community_id
                    community_id += 1
            except Exception:
                for node in comp:
                    community_map[node] = community_id
                community_id += 1
    return community_map


def compute_centralities(G: nx.Graph) -> dict:
    """Compute centrality metrics for all nodes. Returns dict of dicts."""
    if len(G.nodes) == 0:
        return {}

    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G, weight="weight")
    closeness = nx.closeness_centrality(G)
    clustering = nx.clustering(G, weight="weight")

    result = {}
    for node in G.nodes:
        result[node] = {
            "paper_count": G.nodes[node].get("paper_count", 0),
            "affiliation": G.nodes[node].get("affiliation", ""),
            "degree_centrality": round(degree.get(node, 0), 4),
            "betweenness_centrality": round(betweenness.get(node, 0), 4),
            "closeness_centrality": round(closeness.get(node, 0), 4),
            "clustering_coefficient": round(clustering.get(node, 0), 4),
        }
    return result


def get_network_stats(G: nx.Graph) -> dict:
    """Compute overall network statistics."""
    if len(G.nodes) == 0:
        return {"nodes": 0, "edges": 0}

    components = list(nx.connected_components(G))
    largest_cc = max(components, key=len)

    return {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "density": round(nx.density(G), 4),
        "connected_components": len(components),
        "largest_component_size": len(largest_cc),
        "avg_clustering": round(nx.average_clustering(G), 4),
    }
