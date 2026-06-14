from app.models.file import File


def validate_citations(answer: str, version_id, db) -> dict:
    files = db.query(File).filter(File.version_id == version_id).all()
    valid_paths = {f.path.replace("\\", "/") for f in files}

    cited = []
    invalid = []
    for path in valid_paths:
        if path in answer or path.split("/")[-1] in answer:
            cited.append(path)

    # Flag obvious hallucination patterns (paths with extensions not in repo)
    import re
    for match in re.findall(r"[\w./\\-]+\.(py|ts|tsx|js)", answer):
        norm = match.replace("\\", "/")
        if norm not in valid_paths and not any(norm.endswith(p.split("/")[-1]) for p in valid_paths):
            invalid.append(norm)

    return {
        "valid_paths_in_answer": cited,
        "invalid_path_mentions": invalid[:5],
        "confidence": "high" if not invalid else "medium",
    }
