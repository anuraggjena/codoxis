import uuid
import tempfile
import shutil
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from git import Repo, GitCommandError

from app.database import get_db
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.auth.oauth_service import get_user_github_token

from app.services.ingestion.pipeline import run_repository_analysis

router = APIRouter(prefix="/ingestion", tags=["github"])

CLONE_DEPTH = 1


def _validate_github_url(repo_url: str) -> str:
    parsed = urlparse(repo_url.strip())

    if parsed.scheme != "https" or parsed.netloc != "github.com":
        raise HTTPException(status_code=400, detail="Only github.com HTTPS URLs are allowed")

    path = parsed.path.strip("/")
    if not path or ".." in path.split("/") or path.count("/") != 1:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    return f"https://github.com/{path}"


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

    safe_url = _validate_github_url(repo_url)
    temp_dir = tempfile.mkdtemp()
    token = get_user_github_token(current_user.id, db)
    clone_url = safe_url
    if token:
        clone_url = safe_url.replace("https://", f"https://{token}@", 1)

    try:
        try:
            Repo.clone_from(clone_url, temp_dir, depth=CLONE_DEPTH)
        except GitCommandError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {exc}",
            ) from exc

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
        shutil.rmtree(temp_dir, ignore_errors=True)
