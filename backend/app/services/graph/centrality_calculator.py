from app.services.graph.graph_loader import load_graph

def calculate_file_centrality(version_id, db):
    graph = load_graph(version_id, db)

    adjacency = graph["adjacency"]
    reverse = graph["reverse_adjacency"]
    file_map = graph["files"]

    result = []

    for file_id in file_map:
        outgoing = len(adjacency[file_id])
        incoming = len(reverse[file_id])
        score = outgoing + incoming

        result.append({
            "file_id": file_id,
            "file_path": file_map[file_id].path,
            "centrality_score": score,
            "outgoing": outgoing,
            "incoming": incoming,
        })

    result.sort(key=lambda x: x["centrality_score"], reverse=True)

    return result