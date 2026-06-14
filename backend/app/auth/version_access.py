import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.project_version import ProjectVersion


def verify_version_for_user(
    version_id: uuid.UUID,
    current_user: User,
    db: Session,
) -> ProjectVersion:
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    project = db.query(Project).filter(Project.id == version.project_id).first()

    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return version


def get_version_for_user(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectVersion:
    return verify_version_for_user(version_id, current_user, db)


def get_project_for_user(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project
