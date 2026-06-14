from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.edge import Edge
from app.models.file import File
from app.auth.utils import hash_password
from app.services.ingestion.pipeline import run_repository_analysis

FIXTURE = Path(__file__).parent / "fixtures" / "import_repo"


def test_import_resolver_v2_creates_package_edge(db):
    user = User(email="imp@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="import-test")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    run_repository_analysis(str(FIXTURE), version.id, project.id, db)

    files = {f.path.replace("\\", "/"): f for f in db.query(File).filter(File.version_id == version.id).all()}
    edges = db.query(Edge).filter(Edge.version_id == version.id, Edge.relation_type == "file_import").all()

    assert any("main.py" in files[p].path for p in files)
    assert len(edges) >= 1
