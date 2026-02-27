from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.graph.impact_analyzer import analyze_refactor_impact
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.graph.graph_builder import build_graph
from app.services.analysis.explanation_engine import generate_architecture_explanation
from app.models.project_version import ProjectVersion
from app.models.metric import Metric
from app.services.graph.graph_summary import build_graph_summary
from app.services.analysis.version_comparator import compare_versions
from app.services.analysis.risk_analyzer import detect_high_risk_files

router = APIRouter()


@router.get("/impact/{version_id}/{file_id}")
def get_refactor_impact(version_id: str, file_id: str, db: Session = Depends(get_db)):
    result = analyze_refactor_impact(version_id, file_id, db)

    return {
        "file_id": file_id,
        **result
    }

@router.get("/centrality/{version_id}")
def get_centrality(version_id: str, db: Session = Depends(get_db)):
    result = calculate_file_centrality(version_id, db)

    return {
        "version_id": version_id,
        "files_ranked_by_centrality": result
    }

@router.get("/dashboard/{version_id}")
def get_dashboard(version_id: str, db: Session = Depends(get_db)):
    dashboard = build_dashboard(version_id, db)

    if not dashboard:
        return {"error": "Version not found"}

    return dashboard

@router.get("/graph/{version_id}")
def get_graph(version_id: str, db: Session = Depends(get_db)):
    graph = build_graph(version_id, db)

    return graph

@router.get("/explain/{version_id}")
def explain_architecture(version_id: str, db: Session = Depends(get_db)):
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id
    ).first()

    metrics = db.query(Metric).filter(
        Metric.version_id == version_id
    ).first()

    if not version or not metrics:
        return {"error": "Data not found"}

    return generate_architecture_explanation(version, metrics)

@router.get("/graph-summary/{version_id}")
def get_graph_summary(version_id: str, db: Session = Depends(get_db)):
    summary = build_graph_summary(version_id, db)
    return summary

@router.get("/compare/{version_id_1}/{version_id_2}")
def compare_two_versions(
    version_id_1: str,
    version_id_2: str,
    db: Session = Depends(get_db)
):
    result = compare_versions(version_id_1, version_id_2, db)

    if not result:
        return {"error": "One or both versions not found"}

    return result

@router.get("/high-risk/{version_id}")
def get_high_risk_files(version_id: str, db: Session = Depends(get_db)):
    results = detect_high_risk_files(version_id, db)

    return {
        "version_id": version_id,
        "high_risk_files": results[:10]  # Top 10
    }