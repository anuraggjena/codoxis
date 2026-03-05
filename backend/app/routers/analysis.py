from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid
from app.database import SessionLocal
from app.services.analysis.timeline_service import get_architecture_timeline
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
from app.services.analysis.timeline_ai_service import explain_architecture_timeline

router = APIRouter(prefix="/analysis", tags=["analysis"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

@router.get("/timeline/{project_id}")
def architecture_timeline(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    timeline = get_architecture_timeline(project_id, db)

    return {
        "project_id": project_id,
        "timeline": timeline
    }

from app.services.analysis.timeline_service import get_architecture_timeline
from app.services.ai.ai_provider import generate_ai_response


def build_timeline_prompt(timeline):

    prompt = f"""
You are a senior software architect.

Below is architecture evolution data for a software project.

Timeline Data:
{timeline}

Your job:

1. Explain how the architecture changed across versions
2. Identify when architecture quality improved or degraded
3. Explain the likely causes (coupling, dependency depth, circular dependencies)
4. Provide suggestions for improving architecture

Explain clearly so both beginner and experienced developers can understand.
"""

    return prompt


@router.get("/timeline-ai/{project_id}")
def architecture_timeline_ai(
    project_id: uuid.UUID,
    db: Session = Depends(get_db)
):

    result = explain_architecture_timeline(project_id, db)

    return {
        "project_id": project_id,
        **result
    }