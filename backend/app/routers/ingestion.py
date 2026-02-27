import os
import zipfile
import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import SessionLocal
from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.file import File as FileModel
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.parser.parser import parse_file_content

router = APIRouter(prefix="/ingestion", tags=["ingestion"])

SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".html", ".css"}

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


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
    # Check project ownership
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == current_user.id)
        .first()
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")

    # Create new version
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

    # Save uploaded zip
    zip_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.zip")

    with open(zip_path, "wb") as buffer:
        buffer.write(await file.read())

    # Extract
    extract_path = os.path.join(UPLOAD_DIR, str(uuid.uuid4()))
    os.makedirs(extract_path, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)

    # Walk files
    for root, _, files in os.walk(extract_path):
        for filename in files:
            ext = Path(filename).suffix

            if ext in SUPPORTED_EXTENSIONS:
                full_path = os.path.join(root, filename)

                relative_path = os.path.relpath(full_path, extract_path)

                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.readlines()

                file_model = FileModel(
                    version_id=version.id,
                    path=relative_path,
                    language=ext.replace(".", ""),
                    loc=len(content),
                )

                db.add(file_model)

                parse_file_content(file_model, content, db)

    db.commit()

    return {
        "message": "Repository uploaded and files indexed",
        "version_id": version.id,
        "version_number": version.version_number,
    }