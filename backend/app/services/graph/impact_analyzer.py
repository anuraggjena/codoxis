from collections import deque
from app.services.graph.graph_loader import load_graph

def analyze_refactor_impact(version_id, file_id, db):
    graph = load_graph(version_id, db)
    adjacency = graph["adjacency"]
    file_map = graph["files"]

    visited = set()
    queue = deque([(file_id, 0)])

    impacted = []

    while queue:
        current, depth = queue.popleft()

        for neighbor in adjacency[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, depth + 1))

                impacted.append({
                    "file_id": neighbor,
                    "file_path": file_map[neighbor].path,
                    "depth": depth + 1
                })

    impacted.sort(key=lambda x: x["depth"])

    return {
        "impacted_files": impacted,
        "impact_count": len(impacted),
        "max_depth": max([i["depth"] for i in impacted], default=0)
    }