from collections import defaultdict
from app.models.edge import Edge
from app.models.symbol import Symbol


def calculate_coupling_score(version_id, db):
    """
    Calculates average outgoing dependencies per file.
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

    if not adjacency:
        return 0

    total_dependencies = sum(len(neighbors) for neighbors in adjacency.values())
    total_files = len(adjacency)

    return total_dependencies / total_files