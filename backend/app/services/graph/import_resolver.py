import os
from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge


def resolve_imports(version_id, db):
    files = db.query(File).filter(File.version_id == version_id).all()

    # Build full path lookup
    path_map = {}
    module_map = {}

    for f in files:
        normalized_path = f.path.replace("\\", "/")
        path_map[normalized_path] = f.id

        module_name = os.path.splitext(normalized_path)[0].replace("/", ".")
        module_map[module_name] = f.id

    import_symbols = (
        db.query(Symbol)
        .join(File)
        .filter(File.version_id == version_id, Symbol.type == "import")
        .all()
    )

    for imp in import_symbols:
        source_file = db.query(File).filter(File.id == imp.file_id).first()
        if not source_file:
            continue

        import_text = imp.name.strip()

        # --- Python style ---
        if import_text.startswith("from") or import_text.startswith("import"):
            parts = import_text.replace(",", " ").split()

            for part in parts:
                if part in module_map:
                    create_file_edge(
                        version_id,
                        source_file.id,
                        module_map[part],
                        db
                    )

        # --- JS relative imports ---
        if "./" in import_text or "../" in import_text:
            resolved_path = resolve_relative_path(
                source_file.path,
                import_text,
                path_map
            )

            if resolved_path:
                create_file_edge(
                    version_id,
                    source_file.id,
                    path_map[resolved_path],
                    db
                )

    db.commit()


def resolve_relative_path(source_path, import_text, path_map):
    base_dir = os.path.dirname(source_path)

    for token in import_text.split():
        if token.startswith("./") or token.startswith("../"):
            candidate = os.path.normpath(
                os.path.join(base_dir, token)
            ).replace("\\", "/")

            for ext in [".py", ".js", ".ts", ".tsx"]:
                full_candidate = candidate + ext
                if full_candidate in path_map:
                    return full_candidate

    return None


def create_file_edge(version_id, source_file_id, target_file_id, db):
    db.add(Edge(
        version_id=version_id,
        source_file_id=source_file_id,
        target_file_id=target_file_id,
        relation_type="file_import",
    ))