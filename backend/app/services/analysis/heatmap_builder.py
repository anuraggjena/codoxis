from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.graph.centrality_calculator import calculate_file_centrality


def build_heatmap(version_id, db) -> dict:
    risk_map = {r["file_path"]: r["risk_score"] for r in detect_high_risk_files(version_id, db)}
    cent_map = {c["file_path"]: c["centrality_score"] for c in calculate_file_centrality(version_id, db)}
    paths = set(risk_map) | set(cent_map)

    if not paths:
        return {"nodes": [], "max_heat": 0}

    max_risk = max(risk_map.values(), default=1) or 1
    max_cent = max(cent_map.values(), default=1) or 1

    nodes = []
    max_heat = 0
    for path in paths:
        r = risk_map.get(path, 0) / max_risk
        c = cent_map.get(path, 0) / max_cent
        heat = round((r * 0.6 + c * 0.4), 4)
        max_heat = max(max_heat, heat)
        nodes.append({"file_path": path, "heat": heat, "risk_norm": round(r, 4), "centrality_norm": round(c, 4)})

    nodes.sort(key=lambda x: x["heat"], reverse=True)
    return {"nodes": nodes, "max_heat": max_heat}
