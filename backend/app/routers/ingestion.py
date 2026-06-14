import os
import zipfile
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import SessionLocal
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.auth.dependencies import get_current_user
from app.models.user import User

from app.services.ingestion.pipeline import run_repository_analysis

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

UPLOAD_DIR = "temp_uploads"
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
os.makedirs(UPLOAD_DIR, exist_ok=True)


def safe_extract(zip_ref, extract_path):
    extract_abs = os.path.abspath(extract_path)
    for member in zip_ref.namelist():
        member_path = os.path.normpath(os.path.join(extract_path, member))
        if not member_path.startswith(extract_abs):
            raise HTTPException(status_code=400, detail="Unsafe zip entry detected")
    zip_ref.extractall(extract_path)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload/{project_id}")
async def upload_zip(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -------- CHECK PROJECT OWNERSHIP --------
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")

    # -------- CREATE VERSION --------
    version_count = (
        db.query(ProjectVersion)
        .filter(ProjectVersion.project_id == project_id)
        .count()
    )

    version = ProjectVersion(
        project_id=project_id,
        version_number=version_count + 1,
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    # -------- SAVE ZIP --------
    zip_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.zip")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    with open(zip_path, "wb") as buffer:
        buffer.write(content)

    # -------- EXTRACT ZIP --------
    extract_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()))
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        safe_extract(zip_ref, extract_path)

    try:
        # -------- RUN ANALYSIS PIPELINE --------
        analysis_result = run_repository_analysis(
            repo_path=extract_path,
            version_id=version.id,
            project_id=project.id,
            db=db
        )

        return {
            "message": "Repository processed successfully",
            "version_id": version.id,
            "version_number": version.version_number,
            **analysis_result
        }

    finally:
        # -------- CLEAN TEMP FILES --------
        if os.path.exists(zip_path):
            os.remove(zip_path)

        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
