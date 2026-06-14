from app.services.graph.graph_loader import load_graph
from app.services.graph.pagerank_calculator import compute_pagerank


def calculate_file_centrality(version_id, db):
    graph = load_graph(version_id, db)

    adjacency = graph["adjacency"]
    reverse = graph["reverse_adjacency"]
    file_map = graph["files"]
    pagerank = compute_pagerank(version_id, db)

    result = []

    for file_id in file_map:
        outgoing = len(adjacency[file_id])
        incoming = len(reverse[file_id])
        degree_score = outgoing + incoming
        pr = pagerank.get(file_id, 0.0)

        result.append({
            "file_id": file_id,
            "file_path": file_map[file_id].path,
            "centrality_score": round(pr * 100, 4),
            "degree_score": degree_score,
            "pagerank_score": round(pr, 6),
            "outgoing": outgoing,
            "incoming": incoming,
        })

    result.sort(key=lambda x: x["centrality_score"], reverse=True)

    return result
