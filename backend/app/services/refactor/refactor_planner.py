import json
from datetime import datetime, timezone

from app.services.refactor.context_builder import build_refactor_context
from app.services.refactor.rule_engine import prioritize_refactor_candidates
from app.services.ai.refactor_prompt_builder import build_refactor_prompt
from app.services.ai.ai_provider import generate_ai_response
from app.services.refactor.schemas import (
    RefactorPlanResponse,
    RefactorRecommendation,
    RefactorEvidence,
)


def _candidates_to_recommendations(candidates: list) -> list[RefactorRecommendation]:
    recs = []
    for c in candidates:
        evidence_data = c.get("evidence", {})
        recs.append(RefactorRecommendation(
            priority=c["priority"],
            title=c["title"],
            category=c["category"],
            severity=c["severity"],
            affected_files=c["affected_files"],
            evidence=RefactorEvidence(
                cycle_path=evidence_data.get("cycle_path"),
                centrality_scores=evidence_data.get("centrality_scores", {}),
                impact_radius=evidence_data.get("impact_radius"),
                metrics_contribution=evidence_data.get("metrics_contribution", {}),
            ),
            recommended_action=c["recommended_action"],
            beginner_explanation=c["beginner_explanation"],
            estimated_ahs_impact=c["estimated_ahs_impact"],
        ))
    return recs


def generate_refactor_plan(version_id, db, mode: str = "advanced", limit: int = 10) -> RefactorPlanResponse | None:
    context = build_refactor_context(version_id, db)
    if not context:
        return None

    candidates = prioritize_refactor_candidates(context, limit=limit)
    ai_enhanced = False
    summary = f"Found {len(candidates)} refactor opportunities based on graph analysis."

    ai_response = generate_ai_response(
        build_refactor_prompt(context, candidates, mode),
        max_tokens=2000,
    )

    if ai_response:
        try:
            parsed = json.loads(ai_response)
            summary = parsed.get("summary", summary)
            ai_recs = parsed.get("recommendations", [])
            for i, c in enumerate(candidates):
                if i < len(ai_recs):
                    c["recommended_action"] = ai_recs[i].get("recommended_action", c["recommended_action"])
                    c["beginner_explanation"] = ai_recs[i].get("beginner_explanation", c["beginner_explanation"])
                    c["title"] = ai_recs[i].get("title", c["title"])
            ai_enhanced = True
        except json.JSONDecodeError:
            pass

    recommendations = _candidates_to_recommendations(candidates)

    return RefactorPlanResponse(
        version_id=str(version_id),
        mode=mode,
        architecture_score=context["dashboard"]["version_info"].get("architecture_score"),
        data_quality=context["data_quality"],
        summary=summary,
        recommendations=recommendations,
        ai_enhanced=ai_enhanced,
        generated_at=datetime.now(timezone.utc),
    )
