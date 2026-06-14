from app.services.analysis.evolution.graph_diff import build_evolution_diff
from app.services.analysis.evolution.version_pair import get_previous_version


def analyze_commit_impact(version_id, db) -> dict | None:
    from app.models.project_version import ProjectVersion

    target = db.query(ProjectVersion).filter(ProjectVersion.id == version_id).first()
    base = get_previous_version(version_id, db)
    if not target or not base:
        return None

    diff = build_evolution_diff(target, base, db)

    return {
        "version_id": str(version_id),
        "commit_sha": target.commit_sha,
        "commit_message": target.commit_message,
        "summary": diff.summary.model_dump(),
        "top_edge_changes": [e.model_dump() for e in diff.edge_changes[:10]],
        "metric_attribution": [a.model_dump() for a in diff.metric_attribution],
    }
