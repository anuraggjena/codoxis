from app.models.file import File
from app.models.edge import Edge
from app.services.graph.centrality_calculator import calculate_file_centrality


def build_graph(version_id, db):
    """
    Returns graph structure ready for visualization.
    """

    # --- Fetch files ---
    files = db.query(File).filter(
        File.version_id == version_id
    ).all()

    # --- Get centrality for sizing ---
    centrality_list = calculate_file_centrality(version_id, db)
    centrality_map = {
        item["file_id"]: item["centrality_score"]
        for item in centrality_list
    }

    # --- Build nodes ---
    nodes = []
    for file in files:
        nodes.append({
            "id": str(file.id),
            "label": file.path.split("/")[-1],
            "full_path": file.path,
            "centrality": centrality_map.get(file.id, 0),
        })

    # --- Fetch edges ---
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None)
    ).all()

    edge_list = []
    for edge in edges:
        edge_list.append({
            "source": str(edge.source_file_id),
            "target": str(edge.target_file_id),
            "type": edge.relation_type,
        })

    return {
        "nodes": nodes,
        "edges": edge_list
    }