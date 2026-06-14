CATEGORY_WEIGHTS = {
    "circular_dependency": 0.30,
    "high_risk": 0.25,
    "high_centrality": 0.20,
    "drift_regression": 0.15,
    "high_coupling": 0.10,
}


def prioritize_refactor_candidates(context: dict, limit: int = 10) -> list[dict]:
    scored = []

    for path in context.get("cycle_paths", []):
        files = list(dict.fromkeys(path))
        scored.append({
            "score": CATEGORY_WEIGHTS["circular_dependency"],
            "category": "circular_dependency",
            "severity": "high",
            "affected_files": files,
            "evidence": {"cycle_path": path},
            "title": f"Break circular dependency involving {files[0]}",
            "recommended_action": f"Decouple modules: {' → '.join(files)}",
            "beginner_explanation": "Some files depend on each other in a loop, making changes risky.",
            "estimated_ahs_impact": "high",
        })

    for item in context.get("high_risk_files", [])[:10]:
        scored.append({
            "score": CATEGORY_WEIGHTS["high_risk"] * item.get("risk_score", 0.5),
            "category": "high_risk",
            "severity": "high" if item.get("risk_score", 0) > 0.7 else "medium",
            "affected_files": [item["file_path"]],
            "evidence": {
                "impact_radius": item.get("impact_depth"),
                "metrics_contribution": {"risk_score": item.get("risk_score", 0)},
            },
            "title": f"Reduce risk in {item['file_path']}",
            "recommended_action": f"Refactor {item['file_path']} to reduce coupling and impact radius.",
            "beginner_explanation": "This file is central to your project and changes here affect many other parts.",
            "estimated_ahs_impact": "medium",
        })

    if context.get("drift") and context["drift"].get("ahs_change", 0) < 0:
        scored.append({
            "score": CATEGORY_WEIGHTS["drift_regression"],
            "category": "drift_regression",
            "severity": "medium",
            "affected_files": [],
            "evidence": {"metrics_contribution": context["drift"]},
            "title": "Address architecture score regression since last version",
            "recommended_action": "Review recent changes that increased coupling or introduced cycles.",
            "beginner_explanation": "Your architecture health got worse since the last upload.",
            "estimated_ahs_impact": "medium",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    results = []
    for i, item in enumerate(scored[:limit]):
        item["priority"] = i + 1
        results.append(item)

    return results
