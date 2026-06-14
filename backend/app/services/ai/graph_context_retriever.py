from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.graph.cycle_detector import find_cycle_paths
from app.services.graph.dependency_reasoner import find_dependency_paths
from app.services.dashboard.dashboard_service import build_dashboard


def retrieve_graph_context(version_id, db, question: str) -> dict:
    dashboard = build_dashboard(version_id, db) or {}
    high_risk = detect_high_risk_files(version_id, db)[:5]
    cycles = find_cycle_paths(version_id, db, max_paths=3)
    centrality = calculate_file_centrality(version_id, db)[:5]

    evidence = []
    eid = 0

    for f in high_risk:
        eid += 1
        evidence.append({
            "evidence_id": f"risk_{eid}",
            "type": "high_risk_file",
            "data": f,
        })

    for i, cyc in enumerate(cycles):
        evidence.append({
            "evidence_id": f"cycle_{i+1}",
            "type": "cycle_path",
            "data": {"path": cyc},
        })

    for i, c in enumerate(centrality[:3]):
        evidence.append({
            "evidence_id": f"centrality_{i+1}",
            "type": "critical_file",
            "data": c,
        })

    # Simple dependency question: "why does X depend on Y"
    tokens = question.lower().replace("?", "").split()
    if "depend" in tokens and "on" in tokens:
        try:
            idx = tokens.index("on")
            if idx >= 2:
                to_guess = tokens[idx + 1]
                from_guess = tokens[idx - 1]
                path_result = find_dependency_paths(version_id, db, from_guess, to_guess)
                if path_result and path_result.get("shortest_path"):
                    evidence.append({
                        "evidence_id": "dependency_path_1",
                        "type": "dependency_path",
                        "data": path_result,
                    })
        except (ValueError, IndexError):
            pass

    return {
        "question": question,
        "architecture_score": dashboard.get("version_info", {}).get("architecture_score"),
        "metrics": dashboard.get("metrics", {}),
        "graph_quality": dashboard.get("graph_quality"),
        "evidence": evidence,
    }
