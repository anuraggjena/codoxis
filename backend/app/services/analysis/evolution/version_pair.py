from app.models.project_version import ProjectVersion


def get_previous_version(version_id, db) -> ProjectVersion | None:
    current = db.query(ProjectVersion).filter(ProjectVersion.id == version_id).first()
    if not current or current.version_number <= 1:
        return None
    return (
        db.query(ProjectVersion)
        .filter(
            ProjectVersion.project_id == current.project_id,
            ProjectVersion.version_number == current.version_number - 1,
        )
        .first()
    )
