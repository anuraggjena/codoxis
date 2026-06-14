from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.graph.cycle_detector import find_cycle_paths


def compute_technical_debt(version_id, db) -> dict:
    risk_files = {r["file_path"]: r for r in detect_high_risk_files(version_id, db)}
    centrality = {c["file_path"]: c for c in calculate_file_centrality(version_id, db)}
    cycles = find_cycle_paths(version_id, db)
    files_in_cycles = set()
    for c in cycles:
        files_in_cycles.update(c)

    file_scores = []
    all_paths = set(risk_files) | set(centrality)

    for path in all_paths:
        risk = risk_files.get(path, {}).get("risk_score", 0)
        cent = centrality.get(path, {}).get("centrality_score", 0) / 100
        in_cycle = 1.0 if path in files_in_cycles else 0.0
        tds = round((risk * 0.5) + (cent * 0.35) + (in_cycle * 0.15), 4)
        file_scores.append({
            "file_path": path,
            "technical_debt_score": tds,
            "in_cycle": bool(in_cycle),
            "risk_score": risk,
        })

    file_scores.sort(key=lambda x: x["technical_debt_score"], reverse=True)
    project_tds = round(sum(f["technical_debt_score"] for f in file_scores[:20]) / max(1, min(20, len(file_scores))), 4)

    return {
        "project_technical_debt_score": project_tds,
        "files": file_scores[:50],
        "files_in_cycles": len(files_in_cycles),
    }
