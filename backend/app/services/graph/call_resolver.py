from uuid import UUID

from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge


def _call_edge_exists(version_id, source_file_id, target_file_id, source_symbol_id, db) -> bool:
    return db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id == source_file_id,
        Edge.target_file_id == target_file_id,
        Edge.source_symbol_id == source_symbol_id,
        Edge.relation_type == "calls",
    ).first() is not None


def resolve_calls(version_id, db) -> dict:
    files = db.query(File).filter(File.version_id == version_id).all()

    # Index top-level functions/classes by name -> [(file_id, symbol_id, type)]
    symbol_index: dict[str, list[tuple[UUID, UUID, str]]] = {}
    for f in files:
        symbols = db.query(Symbol).filter(
            Symbol.file_id == f.id,
            Symbol.type.in_(["function", "class"]),
        ).all()
        for sym in symbols:
            symbol_index.setdefault(sym.name, []).append((f.id, sym.id, sym.type))

    call_symbols = (
        db.query(Symbol)
        .join(File)
        .filter(File.version_id == version_id, Symbol.type == "call")
        .all()
    )

    resolved = 0
    unresolved: list[str] = []

    for call in call_symbols:
        source_file_id = call.file_id
        candidates = symbol_index.get(call.name, [])
        if not candidates:
            unresolved.append(call.name)
            continue

        # Prefer same-file match, else first cross-file
        target = None
        for file_id, sym_id, _ in candidates:
            if file_id == source_file_id:
                target = (file_id, sym_id)
                break
        if target is None:
            for file_id, sym_id, _ in candidates:
                if file_id != source_file_id:
                    target = (file_id, sym_id)
                    break

        if target is None:
            unresolved.append(call.name)
            continue

        target_file_id, target_symbol_id = target
        if _call_edge_exists(version_id, source_file_id, target_file_id, call.id, db):
            resolved += 1
            continue

        db.add(Edge(
            version_id=version_id,
            source_file_id=source_file_id,
            target_file_id=target_file_id,
            source_symbol_id=call.id,
            target_symbol_id=target_symbol_id,
            relation_type="calls",
        ))
        resolved += 1

    db.commit()
    return {
        "total_calls": len(call_symbols),
        "resolved_calls": resolved,
        "unresolved_calls": list(dict.fromkeys(unresolved)),
    }
