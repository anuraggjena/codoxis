from app.services.analysis.timeline_service import get_architecture_timeline


def predict_debt_trajectory(project_id, db) -> dict:
    timeline = get_architecture_timeline(project_id, db)
    if len(timeline) < 2:
        return {"trajectory": "insufficient_data", "message": "Need at least 2 versions."}

    recent = timeline[-3:]
    coupling_rising = all(
        recent[i]["coupling"] is not None
        and recent[i + 1]["coupling"] is not None
        and recent[i + 1]["coupling"] > recent[i]["coupling"]
        for i in range(len(recent) - 1)
    ) if len(recent) >= 2 else False

    ahs_falling = (
        recent[-1]["architecture_score"] is not None
        and recent[0]["architecture_score"] is not None
        and recent[-1]["architecture_score"] < recent[0]["architecture_score"]
    )

    if coupling_rising and ahs_falling:
        trajectory = "worsening"
        message = "Coupling is rising and architecture score is declining across recent versions."
    elif ahs_falling:
        trajectory = "declining"
        message = "Architecture score is trending down."
    else:
        trajectory = "stable"
        message = "No strong negative trend detected."

    return {
        "trajectory": trajectory,
        "message": message,
        "versions_analyzed": len(recent),
    }
