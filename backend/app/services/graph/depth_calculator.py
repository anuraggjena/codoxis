from collections import defaultdict
from app.models.edge import Edge
from app.models.symbol import Symbol


def calculate_dependency_depth(version_id, db):
    """
    Calculates maximum dependency depth at file level.
    """

    adjacency = defaultdict(set)

    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    for edge in edges:
        if edge.source_file_id != edge.target_file_id:
            adjacency[edge.source_file_id].add(edge.target_file_id)

    max_depth = 0

    def dfs(node, visited):
        nonlocal max_depth
        visited.add(node)

        for neighbor in adjacency[node]:
            if neighbor not in visited:
                dfs(neighbor, visited)

        max_depth = max(max_depth, len(visited))
        visited.remove(node)

    for node in adjacency:
        dfs(node, set())

    return max_depth