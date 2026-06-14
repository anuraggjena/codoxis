from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.version_access import get_version_for_user
from app.models.project_version import ProjectVersion
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.ai.architecture_ai import generate_architecture_analysis
from app.services.ai.architecture_chat import answer_architecture_question
from app.services.ai.code_assistant import analyze_code_snippet
from app.services.refactor.refactor_planner import generate_refactor_plan
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/architecture-report/{version_id}")
def ai_architecture_report(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = "advanced",
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    analysis = generate_architecture_analysis(dashboard, mode)

    return {
        "version_id": str(version.id),
        "mode": mode,
        "analysis": analysis,
    }


@router.get("/ask/{version_id}")
def ask_architecture_ai(
    version: ProjectVersion = Depends(get_version_for_user),
    question: str = "",
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    answer = answer_architecture_question(dashboard, question)

    return {
        "version_id": str(version.id),
        "question": question,
        "answer": answer,
    }


@router.post("/code-help")
def code_help(
    code: str,
    question: str,
    current_user: User = Depends(get_current_user),
):
    response = analyze_code_snippet(code, question)

    return {
        "question": question,
        "analysis": response,
    }


@router.get("/refactor-plan/{version_id}")
def get_refactor_plan(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = Query(default="advanced", pattern="^(beginner|advanced)$"),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    plan = generate_refactor_plan(version.id, db, mode=mode, limit=limit)

    if not plan:
        raise HTTPException(status_code=404, detail="Analysis incomplete")

    return plan.model_dump()
