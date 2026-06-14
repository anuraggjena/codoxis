import json

from app.services.analysis.evolution.graph_diff import build_evolution_diff
from app.services.analysis.evolution.schemas import RootCauseItem, RootCauseResponse
from app.services.analysis.evolution.version_pair import get_previous_version
from app.services.ai.ai_provider import generate_ai_response


def build_root_cause_bundle(version_id, db) -> dict | None:
    from app.models.project_version import ProjectVersion

    target = db.query(ProjectVersion).filter(ProjectVersion.id == version_id).first()
    base = get_previous_version(version_id, db)
    if not target or not base:
        return None

    diff = build_evolution_diff(target, base, db)
    return {
        "diff": diff.model_dump(),
        "evidence_index": {
            f"attribution_{a.rank}": a.model_dump()
            for a in diff.metric_attribution
        },
    }


def generate_root_cause_analysis(version_id, db, mode: str = "advanced") -> RootCauseResponse | None:
    bundle = build_root_cause_bundle(version_id, db)
    if not bundle:
        return None

    diff = bundle["diff"]
    from app.services.ai.root_cause_prompt_builder import build_root_cause_prompt

    prompt = build_root_cause_prompt(diff, mode)
    raw = generate_ai_response(prompt, max_tokens=1500)

    headline = "Architecture metrics changed between versions."
    causes: list[RootCauseItem] = []

    if raw:
        try:
            parsed = json.loads(raw)
            headline = parsed.get("headline", headline)
            for item in parsed.get("root_causes", []):
                causes.append(RootCauseItem(**item))
        except json.JSONDecodeError:
            headline = raw[:200]

    if not causes:
        for a in diff.get("metric_attribution", []):
            causes.append(RootCauseItem(
                title=a["factor"].replace("_", " ").title(),
                severity="high" if a["contribution_estimate"] >= 0.35 else "medium",
                evidence_refs=[a.get("evidence_id", f"attribution_{a['rank']}")],
                explanation=str(a.get("evidence", {})),
                recommended_action="Review the listed dependency changes and decouple where possible.",
            ))

    return RootCauseResponse(
        version_id=str(version_id),
        headline=headline,
        root_causes=causes,
        confidence="high" if diff.get("data_quality") == "high" else "medium",
        data_quality_note=f"Graph quality: {diff.get('data_quality', 'unknown')}",
    )
