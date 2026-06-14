import uuid
from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.file import File
from app.models.symbol import Symbol
from app.services.ingestion.pipeline import run_repository_analysis
from app.auth.utils import hash_password

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_repo"


def test_pipeline_parses_files_and_symbols(db):
    user = User(email="test@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="test-project")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    result = run_repository_analysis(
        repo_path=str(FIXTURE_PATH),
        version_id=version.id,
        project_id=project.id,
        db=db,
    )

    files = db.query(File).filter(File.version_id == version.id).all()
    symbols = (
        db.query(Symbol)
        .join(File)
        .filter(File.version_id == version.id)
        .all()
    )

    assert len(files) == 2
    assert len(symbols) >= 2
    assert all(f.hash for f in files), "every ingested file must have a content hash"
    assert len({f.hash for f in files}) == len(files), "hashes must differ for distinct files"
    assert "architecture_score" in result
    assert result["architecture_score"] is not None
