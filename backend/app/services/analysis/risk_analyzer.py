from app.services.graph.graph_loader import load_graph
from app.services.graph.centrality_calculator import calculate_file_centrality


def detect_high_risk_files(version_id, db):
    graph = load_graph(version_id, db)

    adjacency = graph["adjacency"]
    reverse = graph["reverse_adjacency"]
    file_map = graph["files"]

    # --- Centrality (already optimized)
    centrality_data = calculate_file_centrality(version_id, db)
    centrality_map = {
        item["file_id"]: item["centrality_score"]
        for item in centrality_data
    }

    max_centrality = max(centrality_map.values(), default=1)
    max_incoming = max([len(reverse[fid]) for fid in file_map], default=1)
    total_files = len(file_map) or 1

    results = []

    for file_id in file_map:

        # --- Impact depth (compute directly from adjacency, no recursive DB calls)
        visited = set()
        stack = [(file_id, 0)]
        max_depth = 0

        while stack:
            current, depth = stack.pop()

            for neighbor in adjacency[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, depth + 1))
                    max_depth = max(max_depth, depth + 1)

        # --- Normalize metrics
        normalized_centrality = centrality_map.get(file_id, 0) / max_centrality
        normalized_impact = max_depth / total_files
        normalized_incoming = len(reverse[file_id]) / max_incoming if max_incoming else 0

        # --- Weighted risk score
        risk_score = (
            (normalized_centrality * 0.4) +
            (normalized_impact * 0.35) +
            (normalized_incoming * 0.25)
        )

        results.append({
            "file_id": file_id,
            "file_path": file_map[file_id].path,
            "risk_score": round(risk_score, 3),
            "impact_depth": max_depth,
            "centrality": centrality_map.get(file_id, 0),
            "incoming_dependencies": len(reverse[file_id]),
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)

    return results