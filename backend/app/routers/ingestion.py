import os
import zipfile
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import get_db, SessionLocal
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.services.ingestion.pipeline import run_repository_analysis
from app.services.ingestion.git_history import import_commits
from app.services.ingestion.job_runner import create_job, get_job, update_job

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

UPLOAD_DIR = "temp_uploads"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)


def safe_extract(zip_ref, extract_path):
    extract_abs = os.path.abspath(extract_path)
    for member in zip_ref.namelist():
        member_path = os.path.abspath(os.path.join(extract_path, member))
        if os.path.commonpath([extract_abs, member_path]) != extract_abs:
            raise HTTPException(status_code=400, detail="Unsafe zip entry detected")
    zip_ref.extractall(extract_path)


def _cleanup_paths(*paths):
    for path in paths:
        if path and os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path, ignore_errors=True)
            else:
                os.remove(path)


def _process_upload(extract_path: str, version_id, project_id, db: Session) -> dict:
    return run_repository_analysis(
        repo_path=extract_path,
        version_id=version_id,
        project_id=project_id,
        db=db,
    )


def _run_upload_job(job_id: str, zip_path: str, extract_path: str, version_id, project_id):
    db = SessionLocal()
    try:
        update_job(job_id, "processing")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            safe_extract(zip_ref, extract_path)
        result = _process_upload(extract_path, version_id, project_id, db)
        version = db.query(ProjectVersion).filter(ProjectVersion.id == version_id).first()
        if version:
            version.ingestion_status = "completed"
            db.commit()
        update_job(job_id, "completed", result={
            "version_id": str(version_id),
            "version_number": version.version_number if version else None,
            **result,
        })
    except Exception as exc:
        version = db.query(ProjectVersion).filter(ProjectVersion.id == version_id).first()
        if version:
            version.ingestion_status = "failed"
            db.commit()
        update_job(job_id, "failed", error=str(exc))
    finally:
        db.close()
        _cleanup_paths(zip_path, extract_path)


@router.post("/upload/{project_id}")
async def upload_zip(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")

    version_count = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .count()
    )

    version = ProjectVersion(
        project_id=project_id,
        version_number=version_count + 1,
        source_type="zip_upload",
        ingestion_status="processing",
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    zip_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.zip")
    extract_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()))

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    with open(zip_path, "wb") as buffer:
        buffer.write(content)

    os.makedirs(extract_path, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            safe_extract(zip_ref, extract_path)

        analysis_result = _process_upload(extract_path, version.id, project.id, db)
        version.ingestion_status = "completed"
        db.commit()

        return {
            "message": "Repository processed successfully",
            "version_id": version.id,
            "version_number": version.version_number,
            **analysis_result,
        }

    except ValueError as exc:
        version.ingestion_status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        _cleanup_paths(zip_path, extract_path)


@router.post("/upload-async/{project_id}")
async def upload_zip_async(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")

    version_count = db.query(ProjectVersion).filter(ProjectVersion.project_id == project_id).count()
    version = ProjectVersion(
        project_id=project_id,
        version_number=version_count + 1,
        source_type="zip_upload",
        ingestion_status="pending",
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    zip_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.zip")
    extract_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()))
    with open(zip_path, "wb") as buffer:
        buffer.write(content)
    os.makedirs(extract_path, exist_ok=True)

    job_id = create_job("zip_upload", metadata={"version_id": str(version.id), "project_id": str(project_id)})
    background_tasks.add_task(_run_upload_job, job_id, zip_path, extract_path, version.id, project.id)

    return {
        "message": "Upload accepted; processing in background",
        "job_id": job_id,
        "version_id": str(version.id),
        "version_number": version.version_number,
    }


@router.post("/github/commits/{project_id}")
def ingest_github_commits(
    project_id: uuid.UUID,
    repo_url: str,
    max_commits: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.auth.oauth_service import get_user_github_token

    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Only github.com HTTPS URLs allowed")

    token = get_user_github_token(current_user.id, db)
    results = import_commits(project_id, repo_url, db, max_commits=max_commits, github_token=token)
    return {"message": "Commits imported", "versions": results}


@router.get("/status/{job_id}")
def ingestion_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
