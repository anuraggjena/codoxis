import uuid
import tempfile
import shutil
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from git import Repo

from app.database import get_db
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.auth.dependencies import get_current_user

from app.services.ingestion.pipeline import run_repository_analysis

router = APIRouter(prefix="/ingestion", tags=["github"])


@router.post("/github/{project_id}")
def import_github_repo(
    project_id: uuid.UUID,
    repo_url: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    temp_dir = tempfile.mkdtemp()

    try:
        Repo.clone_from(repo_url, temp_dir)

        version_count = db.query(ProjectVersion).filter(
            ProjectVersion.project_id == project_id
        ).count()

        version = ProjectVersion(
            project_id=project_id,
            version_number=version_count + 1
        )

        db.add(version)
        db.commit()
        db.refresh(version)

        analysis_result = run_repository_analysis(
            repo_path=temp_dir,
            version_id=version.id,
            project_id=project.id,
            db=db
        )

        return {
            "message": "GitHub repository analyzed successfully",
            "version_id": version.id,
            **analysis_result
        }

    finally:
        shutil.rmtree(temp_dir)