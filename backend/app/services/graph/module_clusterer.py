from collections import defaultdict

from app.models.file import File
from app.models.edge import Edge


def cluster_modules(version_id, db) -> dict:
    files = db.query(File).filter(File.version_id == version_id).all()
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).all()

    id_to_path = {f.id: f.path.replace("\\", "/") for f in files}

    def cluster_key(path: str) -> str:
        parts = path.split("/")
        if len(parts) <= 1:
            return "root"
        return parts[0] if len(parts) == 2 else "/".join(parts[:2])

    clusters: dict[str, list[str]] = defaultdict(list)
    for f in files:
        p = f.path.replace("\\", "/")
        clusters[cluster_key(p)].append(p)

    cluster_ids = {p: cluster_key(p) for p in id_to_path.values()}
    internal = defaultdict(int)
    external = defaultdict(int)

    for e in edges:
        sp = id_to_path.get(e.source_file_id)
        tp = id_to_path.get(e.target_file_id)
        if not sp or not tp:
            continue
        sc = cluster_ids[sp]
        tc = cluster_ids[tp]
        if sc == tc:
            internal[sc] += 1
        else:
            external[sc] += 1
            external[tc] += 1

    result = []
    for i, (label, file_list) in enumerate(sorted(clusters.items())):
        result.append({
            "id": f"cluster_{i}",
            "label": label,
            "files": sorted(file_list),
            "internal_edges": internal[label],
            "external_edges": external[label],
        })

    return {"clusters": result, "cluster_count": len(result)}
