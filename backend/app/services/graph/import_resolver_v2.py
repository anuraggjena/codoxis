import os
from uuid import UUID

from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge
from app.services.graph.import_parser import ImportRef, parse_import


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _build_maps(files: list[File]) -> tuple[dict[str, UUID], dict[str, UUID], dict[str, UUID]]:
    path_map: dict[str, UUID] = {}
    module_map: dict[str, UUID] = {}
    dir_index: dict[str, UUID] = {}  # directory -> __init__.py file if exists

    for f in files:
        normalized = _normalize_path(f.path)
        path_map[normalized] = f.id

        stem = os.path.splitext(normalized)[0]
        module_map[stem.replace("/", ".")] = f.id

        basename = os.path.basename(normalized)
        if basename == "__init__.py":
            pkg_dir = os.path.dirname(stem)
            if pkg_dir:
                module_map[pkg_dir.replace("/", ".")] = f.id
                dir_index[pkg_dir] = f.id
            else:
                module_map[stem.replace("/", ".")] = f.id

    return path_map, module_map, dir_index


def _resolve_relative(ref: ImportRef, source_path: str, path_map: dict[str, UUID]) -> UUID | None:
    source_dir = os.path.dirname(_normalize_path(source_path))
    parts = source_dir.split("/") if source_dir else []

    if ref.relative_module and (ref.relative_module.startswith("./") or ref.relative_module.startswith("../")):
        candidate_base = os.path.normpath(os.path.join(source_dir, ref.relative_module)).replace("\\", "/")
    else:
        up = max(0, ref.relative_segments - 1)
        base_parts = parts[: len(parts) - up] if parts else []
        if ref.relative_module:
            base_parts.extend(ref.relative_module.split("/"))
        candidate_base = "/".join(p for p in base_parts if p)

    candidates = [
        candidate_base,
        candidate_base + ".py",
        candidate_base + ".ts",
        candidate_base + ".tsx",
        candidate_base + ".js",
        os.path.join(candidate_base, "__init__.py").replace("\\", "/"),
        os.path.join(candidate_base, "index.ts").replace("\\", "/"),
        os.path.join(candidate_base, "index.tsx").replace("\\", "/"),
        os.path.join(candidate_base, "index.js").replace("\\", "/"),
    ]

    for c in candidates:
        c = _normalize_path(c)
        if c in path_map:
            return path_map[c]
    return None


def _resolve_module(ref: ImportRef, module_map: dict[str, UUID]) -> UUID | None:
    if not ref.module:
        return None
    mod = ref.module.strip()
    if mod in module_map:
        return module_map[mod]
    # try progressively shorter prefixes: app.services.auth -> app.services -> app
    parts = mod.split(".")
    while len(parts) > 1:
        parts.pop()
        prefix = ".".join(parts)
        if prefix in module_map:
            return module_map[prefix]
    return None


def _edge_exists(version_id, source_id, target_id, db) -> bool:
    return db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id == source_id,
        Edge.target_file_id == target_id,
        Edge.relation_type == "file_import",
    ).first() is not None


def create_file_edge(version_id, source_file_id, target_file_id, db):
    if source_file_id == target_file_id:
        return
    if _edge_exists(version_id, source_file_id, target_file_id, db):
        return
    db.add(Edge(
        version_id=version_id,
        source_file_id=source_file_id,
        target_file_id=target_file_id,
        source_symbol_id=None,
        target_symbol_id=None,
        relation_type="file_import",
    ))


def resolve_imports_v2(version_id, db) -> dict:
    files = db.query(File).filter(File.version_id == version_id).all()
    path_map, module_map, _ = _build_maps(files)

    import_symbols = (
        db.query(Symbol)
        .join(File)
        .filter(File.version_id == version_id, Symbol.type == "import")
        .all()
    )

    resolved = 0
    unresolved: list[str] = []

    for imp in import_symbols:
        source_file = db.query(File).filter(File.id == imp.file_id).first()
        if not source_file:
            continue

        ref = parse_import(imp.name, source_file.path)
        if ref is None:
            unresolved.append(imp.name)
            continue

        target_id = None
        if ref.is_relative:
            target_id = _resolve_relative(ref, source_file.path, path_map)
        else:
            target_id = _resolve_module(ref, module_map)

        if target_id:
            create_file_edge(version_id, source_file.id, target_id, db)
            resolved += 1
        else:
            unresolved.append(imp.name)

    db.commit()
    total = len(import_symbols)
    return {
        "total_imports": total,
        "resolved_imports": resolved,
        "unresolved_imports": unresolved,
    }
