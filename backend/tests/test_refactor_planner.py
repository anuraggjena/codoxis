from pathlib import Path
from unittest.mock import patch

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.ingestion.pipeline import run_repository_analysis
from app.services.refactor.refactor_planner import generate_refactor_plan
from app.auth.utils import hash_password

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_repo"


@patch("app.services.refactor.refactor_planner.generate_ai_response", return_value=None)
def test_generate_refactor_plan_rule_only(mock_ai, db):
    user = User(email="plan@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="plan-test")
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

    plan = generate_refactor_plan(version.id, db, mode="advanced", limit=5)

    assert plan is not None
    assert plan.ai_enhanced is False
    assert plan.version_id == str(version.id)
    assert isinstance(plan.recommendations, list)
