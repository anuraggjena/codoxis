from unittest.mock import patch

import uuid

from app.auth.utils import hash_password, create_access_token
from app.models.user import User


def test_ask_requires_question(client, db):
    from app.models.project import Project
    from app.models.project_version import ProjectVersion
    from app.models.file import File
    from app.models.metric import Metric

    owner = User(email="ask@example.com", hashed_password=hash_password("pass1234"))
    db.add(owner)
    db.commit()

    project = Project(user_id=owner.id, name="p")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1, architecture_score=80.0)
    db.add(version)
    db.commit()

    db.add(File(version_id=version.id, path="main.py", language="py", loc=10))
    db.add(Metric(version_id=version.id, circular_dependencies=0, coupling_score=0.1, dependency_depth=1))
    db.commit()

    token = create_access_token({"sub": str(owner.id)})

    response = client.get(
        f"/ai/ask/{version.id}?question=",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400


@patch("app.services.ai.ai_provider.generate_ai_response", return_value=None)
def test_ask_returns_503_when_ai_unavailable(mock_ai, client, db):
    from app.models.project import Project
    from app.models.project_version import ProjectVersion
    from app.models.file import File
    from app.models.metric import Metric

    owner = User(email="ai@example.com", hashed_password=hash_password("pass1234"))
    db.add(owner)
    db.commit()

    project = Project(user_id=owner.id, name="p")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1, architecture_score=80.0)
    db.add(version)
    db.commit()

    db.add(File(version_id=version.id, path="main.py", language="py", loc=10))
    db.add(Metric(version_id=version.id, circular_dependencies=0, coupling_score=0.1, dependency_depth=1))
    db.commit()

    token = create_access_token({"sub": str(owner.id)})
    response = client.get(
        f"/ai/ask/{version.id}?question=test",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert "AI unavailable" in response.json()["detail"]


def test_explain_returns_404_without_metrics(client, db):
    from app.models.project import Project
    from app.models.project_version import ProjectVersion

    owner = User(email="explain@example.com", hashed_password=hash_password("pass1234"))
    db.add(owner)
    db.commit()

    project = Project(user_id=owner.id, name="p")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    token = create_access_token({"sub": str(owner.id)})
    response = client.get(
        f"/analysis/explain/{version.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
