from collections import defaultdict
from app.models.file import File
from app.models.edge import Edge


def load_graph(version_id, db):
    files = db.query(File).filter(
        File.version_id == version_id
    ).all()

    file_map = {file.id: file for file in files}

    adjacency = defaultdict(set)
    reverse_adjacency = defaultdict(set)

    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    for edge in edges:
        adjacency[edge.source_file_id].add(edge.target_file_id)
        reverse_adjacency[edge.target_file_id].add(edge.source_file_id)

    return {
        "files": file_map,
        "adjacency": adjacency,
        "reverse_adjacency": reverse_adjacency,
        "edges": edges,
    }