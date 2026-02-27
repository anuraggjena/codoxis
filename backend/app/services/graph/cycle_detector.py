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

    for node in adjacency:
        if node not in visited:
            dfs(node)

    return cycle_count