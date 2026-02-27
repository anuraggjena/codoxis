def classify_risk(score):
    if score >= 85:
        return "Healthy"
    elif score >= 70:
        return "Stable"
    elif score >= 50:
        return "Warning"
    else:
        return "Critical"


def generate_architecture_explanation(version, metrics):
    explanation = {}

    # --- Cycle explanation ---
    if metrics.circular_dependencies == 0:
        explanation["cycles"] = "No circular dependencies detected."
    else:
        explanation["cycles"] = f"{metrics.circular_dependencies} circular dependencies detected."

    # --- Coupling explanation ---
    if metrics.coupling_score < 2:
        explanation["coupling"] = "Low coupling observed."
    elif metrics.coupling_score < 5:
        explanation["coupling"] = "Moderate coupling observed."
    else:
        explanation["coupling"] = "High coupling detected. Refactoring recommended."

    # --- Depth explanation ---
    if metrics.dependency_depth < 4:
        explanation["depth"] = "Shallow dependency graph."
    elif metrics.dependency_depth < 8:
        explanation["depth"] = "Moderate dependency depth."
    else:
        explanation["depth"] = "Deep dependency chains detected."

    risk_level = classify_risk(version.architecture_score or 0)

    return {
        "architecture_score": version.architecture_score,
        "risk_level": risk_level,
        "analysis": explanation
    }