from collections import defaultdict
from app.models.edge import Edge
from app.models.symbol import Symbol


def detect_circular_dependencies(version_id, db):
    """
    Detect circular dependencies at file level.
    Returns number of cycles detected.
    """

    # Step 1: Build file-level adjacency graph
    adjacency = defaultdict(set)

    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    for edge in edges:
        if edge.source_file_id != edge.target_file_id:
            adjacency[edge.source_file_id].add(edge.target_file_id)

    # Step 2: DFS cycle detection
    visited = set()
    recursion_stack = set()
    cycle_count = 0

    def dfs(node):
        nonlocal cycle_count
        visited.add(node)
        recursion_stack.add(node)

        for neighbor in adjacency[node]:
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in recursion_stack:
                cycle_count += 1

        recursion_stack.remove(node)

    for node in list(adjacency):
        if node not in visited:
            dfs(node)

    return cycle_count

from app.models.file import File


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
    visited_global = set()

    def dfs(node, path, visited):
        if len(cycles) >= max_paths:
            return
        if node in visited:
            idx = path.index(node)
            cycle_ids = path[idx:] + [node]
            cycle_paths = [file_map[fid] for fid in cycle_ids if fid in file_map]
            if len(cycle_paths) >= 2:
                cycles.append(cycle_paths)
            return
        visited.add(node)
        path.append(node)
        for neighbor in adjacency.get(node, []):
            dfs(neighbor, path, visited.copy())
        path.pop()

    for node in adjacency:
        if node not in visited_global:
            dfs(node, [], set())
            visited_global.add(node)

    return cycles[:max_paths]
