from collections import defaultdict
from app.models.file import File
from app.models.edge import Edge


def build_graph_summary(version_id, db):
    files = db.query(File).filter(
        File.version_id == version_id
    ).all()

    total_nodes = len(files)

    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    total_edges = len(edges)

    adjacency = defaultdict(set)
    reverse_adjacency = defaultdict(set)

    for edge in edges:
        adjacency[edge.source_file_id].add(edge.target_file_id)
        reverse_adjacency[edge.target_file_id].add(edge.source_file_id)

    degrees = []

    for file in files:
        outgoing = len(adjacency[file.id])
        incoming = len(reverse_adjacency[file.id])
        degrees.append(outgoing + incoming)

    average_degree = (
        sum(degrees) / total_nodes if total_nodes > 0 else 0
    )

    max_degree = max(degrees) if degrees else 0

    isolated_files = sum(1 for d in degrees if d == 0)

    # Graph density formula (directed graph)
    possible_edges = total_nodes * (total_nodes - 1)
    density = (
        total_edges / possible_edges if possible_edges > 0 else 0
    )

    return {
        "total_files": total_nodes,
        "total_dependencies": total_edges,
        "graph_density": round(density, 4),
        "average_degree": round(average_degree, 2),
        "max_degree": max_degree,
        "isolated_files": isolated_files,
    }