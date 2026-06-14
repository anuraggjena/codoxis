import os

from app.models.file import File
from app.models.edge import Edge
from app.services.graph.centrality_calculator import calculate_file_centrality

MAX_GRAPH_NODES = int(os.getenv("MAX_GRAPH_NODES", "200"))


def _file_label(path: str) -> str:
    return path.replace("\\", "/").split("/")[-1]


def build_graph(version_id, db):
    """
    Returns graph structure ready for visualization.
    Caps at MAX_GRAPH_NODES highest-centrality files.
    """

    files = db.query(File).filter(
        File.version_id == version_id
    ).all()

    centrality_list = calculate_file_centrality(version_id, db)
    centrality_map = {
        item["file_id"]: item["centrality_score"]
        for item in centrality_list
    }

    nodes = []
    for file in files:
        nodes.append({
            "id": str(file.id),
            "label": _file_label(file.path),
            "full_path": file.path.replace("\\", "/"),
            "centrality": centrality_map.get(file.id, 0),
        })

    nodes.sort(key=lambda n: n["centrality"], reverse=True)
    total_nodes = len(nodes)
    if total_nodes > MAX_GRAPH_NODES:
        nodes = nodes[:MAX_GRAPH_NODES]

    visible_ids = {n["id"] for n in nodes}

    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    edge_list = []
    for edge in edges:
        source = str(edge.source_file_id)
        target = str(edge.target_file_id)
        if source in visible_ids and target in visible_ids:
            edge_list.append({
                "source": source,
                "target": target,
                "type": edge.relation_type,
            })

    result = {
        "nodes": nodes,
        "edges": edge_list,
    }

    if total_nodes > MAX_GRAPH_NODES:
        result["total_nodes"] = total_nodes
        result["truncated"] = True

    return result
