from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.edge import Edge
from app.auth.utils import hash_password
from app.services.ingestion.pipeline import run_repository_analysis

SAMPLE = Path(__file__).parent / "fixtures" / "sample_repo"


def test_call_resolver_cross_file_edge(db):
    user = User(email="call@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="call-test")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    run_repository_analysis(str(SAMPLE), version.id, project.id, db)

    call_edges = db.query(Edge).filter(
        Edge.version_id == version.id,
        Edge.relation_type == "calls",
    ).all()

    assert len(call_edges) >= 1
