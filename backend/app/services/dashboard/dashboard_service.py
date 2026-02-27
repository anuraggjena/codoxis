from app.models.project_version import ProjectVersion
from app.models.metric import Metric
from app.services.graph.graph_loader import load_graph
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.graph.graph_summary import build_graph_summary
from app.services.graph.drift_detector import detect_architecture_drift


def build_dashboard(version_id, db):
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id
    ).first()

    if not version:
        return None

    metrics = db.query(Metric).filter(
        Metric.version_id == version_id
    ).first()

    # --- Load graph once
    graph = load_graph(version_id, db)
    total_files = len(graph["files"])
    total_edges = len(graph["edges"])

    # --- Centrality
    centrality = calculate_file_centrality(version_id, db)
    top_critical_files = centrality[:5]

    # --- Graph summary
    summary = build_graph_summary(version_id, db)

    # --- Drift
    drift = detect_architecture_drift(
        version.project_id,
        version_id,
        db
    )

    return {
        "version_info": {
            "version_id": version.id,
            "version_number": version.version_number,
            "architecture_score": version.architecture_score,
        },
        "metrics": {
            "circular_dependencies": metrics.circular_dependencies if metrics else 0,
            "dependency_depth": metrics.dependency_depth if metrics else 0,
            "coupling_score": metrics.coupling_score if metrics else 0,
            "total_files": total_files,
            "total_dependencies": total_edges,
        },
        "graph_summary": summary,
        "drift": drift,
        "top_critical_files": top_critical_files,
    }