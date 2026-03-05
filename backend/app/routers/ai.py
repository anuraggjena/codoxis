from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.ai.architecture_ai import generate_architecture_analysis

from app.services.ai.architecture_chat import answer_architecture_question
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.ai.code_assistant import analyze_code_snippet

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/architecture-report/{version_id}")
def ai_architecture_report(
    version_id: str,
    mode: str = "advanced",
    db: Session = Depends(get_db)
):

    dashboard = build_dashboard(version_id, db)

    if not dashboard:
        return {"error": "Version not found"}

    analysis = generate_architecture_analysis(dashboard, mode)

    return {
        "version_id": version_id,
        "mode": mode,
        "analysis": analysis
    }

@router.get("/ask/{version_id}")
def ask_architecture_ai(
    version_id: str,
    question: str,
    db: Session = Depends(get_db)
):

    dashboard = build_dashboard(version_id, db)

    if not dashboard:
        return {"error": "Version not found"}

    answer = answer_architecture_question(dashboard, question)

    return {
        "version_id": version_id,
        "question": question,
        "answer": answer
    }

@router.post("/code-help")
def code_help(
    code: str,
    question: str
):

    response = analyze_code_snippet(code, question)

    return {
        "question": question,
        "analysis": response
    }