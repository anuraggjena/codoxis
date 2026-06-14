from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.version_access import get_version_for_user
from app.models.project_version import ProjectVersion
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.ai.architecture_ai import generate_architecture_analysis
from app.services.ai.code_assistant import analyze_code_snippet
from app.services.ai.errors import require_ai_result
from app.services.ai.graph_context_retriever import retrieve_graph_context
from app.services.ai.evidence_prompt_builder import build_evidence_prompt
from app.services.ai.ai_provider import generate_ai_response
from app.services.ai.response_validator import validate_citations
from app.services.analysis.evolution.root_cause_builder import generate_root_cause_analysis
from app.services.refactor.refactor_planner import generate_refactor_plan
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI"])

MAX_CODE_CHARS = 10_000
MAX_QUESTION_CHARS = 500


class CodeHelpRequest(BaseModel):
    code: str = Field(..., max_length=MAX_CODE_CHARS)
    question: str = Field(..., max_length=MAX_QUESTION_CHARS)


class CopilotAskRequest(BaseModel):
    version_id: str
    question: str = Field(..., max_length=MAX_QUESTION_CHARS)
    mode: str = "advanced"


@router.get("/architecture-report/{version_id}")
def ai_architecture_report(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = "advanced",
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    analysis = require_ai_result(
        generate_architecture_analysis(dashboard, mode),
        "architecture report",
    )

    return {
        "version_id": str(version.id),
        "mode": mode,
        "analysis": analysis,
    }


@router.get("/ask/{version_id}")
def ask_architecture_ai(
    version: ProjectVersion = Depends(get_version_for_user),
    question: str = Query(default="", max_length=MAX_QUESTION_CHARS),
    db: Session = Depends(get_db),
):
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question is required")

    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    context = retrieve_graph_context(version.id, db, question)
    prompt = build_evidence_prompt(context, mode="advanced")
    answer = require_ai_result(generate_ai_response(prompt), "architecture Q&A")
    validation = validate_citations(answer, version.id, db)

    return {
        "version_id": str(version.id),
        "question": question,
        "answer": answer,
        "citations": context.get("evidence", []),
        "confidence": validation.get("confidence", "medium"),
    }


@router.post("/code-help")
def code_help(
    body: CodeHelpRequest,
    current_user: User = Depends(get_current_user),
):
    response = require_ai_result(
        analyze_code_snippet(body.code, body.question),
        "code help",
    )

    return {
        "question": body.question,
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


@router.get("/root-cause/{version_id}")
def ai_root_cause(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = Query(default="advanced", pattern="^(beginner|advanced)$"),
    db: Session = Depends(get_db),
):
    result = generate_root_cause_analysis(version.id, db, mode=mode)
    if not result:
        raise HTTPException(status_code=404, detail="No previous version for root cause analysis")
    return result.model_dump()


@router.post("/copilot/ask")
def copilot_ask(
    body: CopilotAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    import uuid as uuid_mod
    try:
        vid = uuid_mod.UUID(body.version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid version_id") from exc

    from app.auth.version_access import verify_version_for_user
    verify_version_for_user(vid, current_user, db)

    context = retrieve_graph_context(vid, db, body.question)
    prompt = build_evidence_prompt(context, mode=body.mode)
    answer = require_ai_result(generate_ai_response(prompt, max_tokens=1500), "copilot")
    validation = validate_citations(answer, vid, db)

    return {
        "version_id": body.version_id,
        "question": body.question,
        "answer": answer,
        "citations": context.get("evidence", []),
        "confidence": validation.get("confidence", "medium"),
    }


@router.get("/copilot/suggestions/{version_id}")
def copilot_suggestions(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db) or {}
    suggestions = [
        "Which file should I refactor first?",
        "What are the biggest architecture risks?",
        "Explain the circular dependencies in this project.",
    ]
    if dashboard.get("drift") and (dashboard["drift"].get("ahs_change") or 0) < 0:
        suggestions.insert(0, "Why did the architecture score decrease since the last version?")
    return {"version_id": str(version.id), "suggestions": suggestions}
