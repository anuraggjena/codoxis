from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge


def build_symbol_graph(version_id, db, file_path: str | None = None) -> dict:
    query = db.query(File).filter(File.version_id == version_id)
    if file_path:
        query = query.filter(File.path == file_path)
    files = query.all()
    file_ids = {f.id for f in files}
    id_to_path = {f.id: f.path for f in files}

    nodes = []
    for f in files:
        symbols = db.query(Symbol).filter(Symbol.file_id == f.id).all()
        for s in symbols:
            if s.type in ("function", "class"):
                nodes.append({
                    "id": str(s.id),
                    "label": s.name,
                    "type": s.type,
                    "file_path": f.path,
                })

    node_ids = {n["id"] for n in nodes}
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.relation_type == "calls",
    ).all()

    edge_list = []
    for e in edges:
        if e.source_file_id in file_ids and e.source_symbol_id and e.target_symbol_id:
            sid = str(e.source_symbol_id)
            tid = str(e.target_symbol_id)
            if sid in node_ids and tid in node_ids:
                edge_list.append({"source": sid, "target": tid, "type": "calls"})

    return {"nodes": nodes, "edges": edge_list}
