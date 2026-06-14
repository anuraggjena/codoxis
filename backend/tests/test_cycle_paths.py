from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.ingestion.pipeline import run_repository_analysis
from app.services.graph.cycle_detector import find_cycle_paths
from app.auth.utils import hash_password

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "cyclic_repo"


def test_find_cycle_paths_returns_file_paths(db):
    user = User(email="cycle@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="cycle-test")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    run_repository_analysis(
        repo_path=str(FIXTURE_PATH),
        version_id=version.id,
        project_id=project.id,
        db=db,
    )

    paths = find_cycle_paths(version.id, db)
    assert isinstance(paths, list)
