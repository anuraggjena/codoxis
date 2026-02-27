from app.models.project_version import ProjectVersion
from app.models.metric import Metric


def detect_architecture_drift(project_id, current_version_id, db):
    """
    Compare current version with previous version.
    Returns drift summary dictionary.
    """

    versions = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.version_number.desc())
        .all()
    )

    if len(versions) < 2:
        return None  # No previous version to compare

    current_version = versions[0]
    previous_version = versions[1]

    current_metrics = db.query(Metric).filter(
        Metric.version_id == current_version.id
    ).first()

    previous_metrics = db.query(Metric).filter(
        Metric.version_id == previous_version.id
    ).first()

    if not current_metrics or not previous_metrics:
        return None

    drift = {
        "ahs_change": current_version.architecture_score - previous_version.architecture_score,
        "circular_dependency_change": current_metrics.circular_dependencies - previous_metrics.circular_dependencies,
        "coupling_change": current_metrics.coupling_score - previous_metrics.coupling_score,
        "depth_change": (current_metrics.dependency_depth or 0) - (previous_metrics.dependency_depth or 0),
    }

    return drift