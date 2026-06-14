from pathlib import Path
from unittest.mock import patch

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.services.ingestion.pipeline import run_repository_analysis
from app.auth.utils import hash_password, create_access_token

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_repo"


def _setup_project(db):
    user = User(email="api@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="api-test")
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

    token = create_access_token({"sub": str(user.id)})
    return version, token


@patch("app.services.refactor.refactor_planner.generate_ai_response", return_value=None)
def test_refactor_plan_endpoint(mock_ai, client, db):
    version, token = _setup_project(db)

    response = client.get(
        f"/ai/refactor-plan/{version.id}?mode=beginner&limit=5",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["version_id"] == str(version.id)
    assert data["mode"] == "beginner"
    assert "recommendations" in data
    assert data["ai_enhanced"] is False


def test_refactor_plan_requires_auth(client, db):
    version, _ = _setup_project(db)
    response = client.get(f"/ai/refactor-plan/{version.id}")
    assert response.status_code == 401
