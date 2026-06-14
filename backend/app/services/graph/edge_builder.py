from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge


def build_edges_for_version(version_id, db):
    files = db.query(File).filter(File.version_id == version_id).all()

    for file_model in files:
        symbols = db.query(Symbol).filter(Symbol.file_id == file_model.id).all()

        functions = [s for s in symbols if s.type == "function"]
        calls = [s for s in symbols if s.type == "call"]

        for call in calls:
            for function in functions:
                if call.name == function.name:
                    db.add(Edge(
                        version_id=version_id,
                        source_file_id=file_model.id,
                        target_file_id=file_model.id,
                        source_symbol_id=function.id,
                        target_symbol_id=call.id,
                        relation_type="calls",
                    ))

    db.commit()
