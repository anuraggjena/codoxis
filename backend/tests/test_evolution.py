from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.auth.utils import hash_password
from app.services.ingestion.pipeline import run_repository_analysis
from app.services.analysis.evolution.version_pair import get_previous_version
from app.services.analysis.evolution.graph_diff import build_evolution_diff

SAMPLE = Path(__file__).parent / "fixtures" / "sample_repo"
CYCLIC = Path(__file__).parent / "fixtures" / "cyclic_repo"


def _setup_project(db, name="evo"):
    user = User(email=f"{name}@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()
    project = Project(user_id=user.id, name=name)
    db.add(project)
    db.commit()
    return project


def test_evolution_diff_detects_changes(db):
    project = _setup_project(db, "evo1")

    v1 = ProjectVersion(project_id=project.id, version_number=1)
    db.add(v1)
    db.commit()
    run_repository_analysis(str(SAMPLE), v1.id, project.id, db)

    v2 = ProjectVersion(project_id=project.id, version_number=2)
    db.add(v2)
    db.commit()
    run_repository_analysis(str(CYCLIC), v2.id, project.id, db)

    diff = build_evolution_diff(v2, v1, db)
    assert diff.summary.files_added + diff.summary.files_modified + diff.summary.files_removed >= 0
    assert diff.base_version_id == str(v1.id)


def test_get_previous_version_none_for_v1(db):
    project = _setup_project(db, "evo2")
    v1 = ProjectVersion(project_id=project.id, version_number=1)
    db.add(v1)
    db.commit()
    assert get_previous_version(v1.id, db) is None
