from collections import defaultdict

from app.models.edge import Edge


def _build_adjacency(version_id, db):
    adjacency = defaultdict(set)
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).all()
    for edge in edges:
        if edge.source_file_id != edge.target_file_id:
            adjacency[edge.source_file_id].add(edge.target_file_id)
    return adjacency


def calculate_dependency_depth(version_id, db):
    adjacency = _build_adjacency(version_id, db)
    nodes = set(adjacency.keys()) | {t for targets in adjacency.values() for t in targets}
    if not nodes:
        return 0

    memo: dict = {}

    def longest_from(node, visiting: frozenset):
        if node in visiting:
            return 0
        if node in memo:
            return memo[node]
        best = 0
        for neighbor in adjacency.get(node, []):
            best = max(best, 1 + longest_from(neighbor, visiting | {node}))
        memo[node] = best
        return best

    return max(longest_from(node, frozenset()) for node in nodes)
