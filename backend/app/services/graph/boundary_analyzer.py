from app.services.graph.module_clusterer import cluster_modules


def analyze_boundaries(version_id, db) -> dict:
    data = cluster_modules(version_id, db)
    violations = []

    for cluster in data["clusters"]:
        ratio = cluster["external_edges"] / max(1, cluster["internal_edges"] + cluster["external_edges"])
        if ratio > 0.6 and cluster["external_edges"] >= 3:
            violations.append({
                "cluster": cluster["label"],
                "type": "high_external_coupling",
                "external_ratio": round(ratio, 3),
                "message": f"Cluster '{cluster['label']}' is heavily coupled to other modules.",
            })

        label = cluster["label"].lower()
        for f in cluster["files"]:
            fl = f.lower()
            if ("frontend" in label or "ui" in label) and ("db" in fl or "database" in fl or "models" in fl):
                violations.append({
                    "cluster": cluster["label"],
                    "type": "layer_violation",
                    "file": f,
                    "message": "UI-layer cluster contains data/persistence file.",
                })

    return {
        "clusters": data["clusters"],
        "violations": violations,
        "violation_count": len(violations),
    }
