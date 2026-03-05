from app.models.project_version import ProjectVersion
from app.models.metric import Metric


def get_architecture_timeline(project_id, db):

    versions = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .order_by(ProjectVersion.version_number)
        .all()
    )

    timeline = []

    for version in versions:

        metric = db.query(Metric).filter(
            Metric.version_id == version.id
        ).first()

        timeline.append({
            "version": version.version_number,
            "version_id": str(version.id),
            "architecture_score": version.architecture_score,
            "coupling": metric.coupling_score if metric else None,
            "dependency_depth": metric.dependency_depth if metric else None,
            "circular_dependencies": metric.circular_dependencies if metric else None
        })

    return timeline