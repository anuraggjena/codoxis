from collections import defaultdict

from app.models.edge import Edge
from app.services.graph.graph_loader import load_graph


def compute_pagerank(version_id, db, damping: float = 0.85, iterations: int = 30) -> dict:
    graph = load_graph(version_id, db)
    file_map = graph["files"]
    adjacency = graph["adjacency"]
    reverse = graph["reverse_adjacency"]

    nodes = list(file_map.keys())
    if not nodes:
        return {}

    n = len(nodes)
    scores = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_scores = {}
        for node in nodes:
            rank = (1 - damping) / n
            for predecessor in reverse[node]:
                out_degree = len(adjacency[predecessor]) or 1
                rank += damping * (scores[predecessor] / out_degree)
            new_scores[node] = rank
        scores = new_scores

    return scores
