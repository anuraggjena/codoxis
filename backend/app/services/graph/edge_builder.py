from app.models.symbol import Symbol
from app.models.edge import Edge


def build_edges_for_version(version_id, db):
    """
    Build graph edges for a given project version.
    """

    # Get all files in this version
    files = db.execute(
        "SELECT id FROM files WHERE version_id = :version_id",
        {"version_id": str(version_id)},
    ).fetchall()

    for file_row in files:
        file_id = file_row[0]

        # Get symbols in this file
        symbols = db.query(Symbol).filter(Symbol.file_id == file_id).all()

        functions = [s for s in symbols if s.type == "function"]
        calls = [s for s in symbols if s.type == "call"]
        imports = [s for s in symbols if s.type == "import"]

        # --- Function Call Edges (Same File) ---
        for call in calls:
            for function in functions:
                if call.name == function.name:
                    db.add(Edge(
                        version_id=version_id,
                        source_symbol_id=function.id,
                        target_symbol_id=call.id,
                        relation_type="calls",
                    ))

        # --- Import Edges (File Level Placeholder) ---
        for imp in imports:
            db.add(Edge(
                version_id=version_id,
                source_symbol_id=imp.id,
                target_symbol_id=imp.id,
                relation_type="imports",
            ))

    db.commit()