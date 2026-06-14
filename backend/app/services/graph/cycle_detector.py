from collections import defaultdict

from app.models.edge import Edge
from app.models.file import File


def detect_circular_dependencies(version_id, db):
    cycles = find_cycle_paths(version_id, db, max_paths=50)
    unique = set()
    for path in cycles:
        if len(path) < 2:
            continue
        core = tuple(sorted(set(path)))
        unique.add(core)
    return len(unique)


def find_cycle_paths(version_id, db, max_paths=10):
    file_map = {
        f.id: f.path
        for f in db.query(File).filter(File.version_id == version_id).all()
    }

    adjacency = defaultdict(set)
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).all()

    for edge in edges:
        if edge.source_file_id != edge.target_file_id:
            adjacency[edge.source_file_id].add(edge.target_file_id)

    cycles = []
    seen_signatures = set()

    def dfs(node, path, visited):
        if len(cycles) >= max_paths:
            return
        if node in visited:
            idx = path.index(node)
            cycle_ids = path[idx:] + [node]
            cycle_paths = [file_map[fid] for fid in cycle_ids if fid in file_map]
            if len(cycle_paths) >= 2:
                sig = tuple(sorted(set(cycle_paths)))
                if sig not in seen_signatures:
                    seen_signatures.add(sig)
                    cycles.append(cycle_paths)
            return
        visited.add(node)
        path.append(node)
        for neighbor in adjacency.get(node, []):
            dfs(neighbor, path, visited.copy())
        path.pop()

    for node in adjacency:
        dfs(node, [], set())

    return cycles[:max_paths]
