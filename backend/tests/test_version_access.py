import uuid

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.auth.utils import hash_password, create_access_token


def test_dashboard_requires_auth(client):
    fake_id = str(uuid.uuid4())
    response = client.get(f"/analysis/dashboard/{fake_id}")
    assert response.status_code == 401


def test_dashboard_denies_wrong_user(client, db):
    owner = User(email="owner@example.com", hashed_password=hash_password("pass1234"))
    other = User(email="other@example.com", hashed_password=hash_password("pass1234"))
    db.add_all([owner, other])
    db.commit()

    project = Project(user_id=owner.id, name="secret")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    token = create_access_token({"sub": str(other.id)})
    response = client.get(
        f"/analysis/dashboard/{version.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
