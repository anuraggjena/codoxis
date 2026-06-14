from app.services.dashboard.dashboard_service import build_dashboard
from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.graph.cycle_detector import find_cycle_paths
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.graph.impact_analyzer import analyze_refactor_impact
from app.services.graph.graph_loader import load_graph


def build_refactor_context(version_id, db) -> dict:
    dashboard = build_dashboard(version_id, db)
    if not dashboard:
        return None

    high_risk = detect_high_risk_files(version_id, db)[:10]
    cycle_paths = find_cycle_paths(version_id, db)
    centrality = calculate_file_centrality(version_id, db)

    graph = load_graph(version_id, db)
    coupling_hotspots = {}
    for file_id, neighbors in graph["adjacency"].items():
        if file_id in graph["files"]:
            coupling_hotspots[graph["files"][file_id].path] = len(neighbors)

    impact_analyses = []
    for item in high_risk[:3]:
        impact = analyze_refactor_impact(version_id, str(item["file_id"]), db)
        impact_analyses.append({
            "file_path": item["file_path"],
            "impact": impact,
        })

    total_edges = len(graph["edges"])
    gq = dashboard.get("graph_quality") or {}
    data_quality = gq.get("quality_tier") or ("high" if total_edges > 0 else "low")

    return {
        "dashboard": dashboard,
        "high_risk_files": high_risk,
        "cycle_paths": cycle_paths,
        "centrality": centrality,
        "drift": dashboard.get("drift"),
        "coupling_hotspots": coupling_hotspots,
        "impact_analyses": impact_analyses,
        "data_quality": data_quality,
    }
