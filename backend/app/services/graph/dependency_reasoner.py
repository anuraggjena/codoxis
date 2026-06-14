from collections import deque

from app.services.graph.graph_loader import load_graph


def find_dependency_paths(version_id, db, from_path: str, to_path: str, max_paths: int = 5):
    graph = load_graph(version_id, db)
    file_map = graph["files"]
    path_to_id = {f.path.replace("\\", "/"): fid for fid, f in file_map.items()}

    from_id = path_to_id.get(from_path.replace("\\", "/"))
    to_id = path_to_id.get(to_path.replace("\\", "/"))
    if not from_id or not to_id:
        return None

    adjacency = graph["adjacency"]
    paths = []
    queue = deque([(from_id, [from_id])])

    while queue and len(paths) < max_paths:
        node, path = queue.popleft()
        if node == to_id and len(path) > 1:
            paths.append([file_map[fid].path for fid in path])
            continue
        if len(path) > 12:
            continue
        for neighbor in adjacency.get(node, []):
            if neighbor not in path:
                queue.append((neighbor, path + [neighbor]))

    shortest = min(paths, key=len) if paths else None
    return {
        "from": from_path,
        "to": to_path,
        "shortest_path": shortest,
        "all_paths": paths,
        "path_count": len(paths),
    }
