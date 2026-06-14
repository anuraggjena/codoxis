import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.version_access import (
    get_version_for_user,
    get_project_for_user,
    verify_version_for_user,
)
from app.models.user import User
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.metric import Metric
from app.services.analysis.timeline_service import get_architecture_timeline
from app.services.graph.impact_analyzer import analyze_refactor_impact
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.graph.graph_builder import build_graph
from app.services.analysis.explanation_engine import generate_architecture_explanation
from app.services.graph.graph_summary import build_graph_summary
from app.services.analysis.version_comparator import compare_versions
from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.analysis.timeline_ai_service import explain_architecture_timeline

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/impact/{version_id}/{file_id}")
def get_refactor_impact(
    file_id: str,
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    result = analyze_refactor_impact(version.id, file_id, db)

    return {
        "file_id": file_id,
        **result
    }


@router.get("/centrality/{version_id}")
def get_centrality(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    result = calculate_file_centrality(version.id, db)

    return {
        "version_id": version.id,
        "files_ranked_by_centrality": result
    }


@router.get("/dashboard/{version_id}")
def get_dashboard(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        return {"error": "Version not found"}

    return dashboard


@router.get("/graph/{version_id}")
def get_graph(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    graph = build_graph(version.id, db)

    return graph


@router.get("/explain/{version_id}")
def explain_architecture(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    metrics = db.query(Metric).filter(
        Metric.version_id == version.id
    ).first()

    if not metrics:
        return {"error": "Data not found"}

    return generate_architecture_explanation(version, metrics)


@router.get("/graph-summary/{version_id}")
def get_graph_summary(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    summary = build_graph_summary(version.id, db)
    return summary


@router.get("/compare/{version_id_1}/{version_id_2}")
def compare_two_versions(
    version_id_1: uuid.UUID,
    version_id_2: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    verify_version_for_user(version_id_1, current_user, db)
    verify_version_for_user(version_id_2, current_user, db)

    result = compare_versions(version_id_1, version_id_2, db)

    if not result:
        return {"error": "One or both versions not found"}

    return result


@router.get("/high-risk/{version_id}")
def get_high_risk_files(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    results = detect_high_risk_files(version.id, db)

    return {
        "version_id": version.id,
        "high_risk_files": results[:10]
    }


@router.get("/timeline/{project_id}")
def architecture_timeline(
    project: Project = Depends(get_project_for_user),
    db: Session = Depends(get_db),
):
    timeline = get_architecture_timeline(project.id, db)

    return {
        "project_id": project.id,
        "timeline": timeline
    }


@router.get("/timeline-ai/{project_id}")
def architecture_timeline_ai(
    project: Project = Depends(get_project_for_user),
    db: Session = Depends(get_db),
):
    result = explain_architecture_timeline(project.id, db)

    return {
        "project_id": project.id,
        **result
    }
