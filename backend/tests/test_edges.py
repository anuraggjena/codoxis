from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.edge import Edge
from app.services.ingestion.pipeline import run_repository_analysis
from app.auth.utils import hash_password


def test_pipeline_creates_file_level_import_edges(db, sample_repo):
    user = User(email="edges@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="edge-test")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    run_repository_analysis(
        repo_path=str(sample_repo),
        version_id=version.id,
        project_id=project.id,
        db=db,
    )

    edges = db.query(Edge).filter(Edge.version_id == version.id).all()
    file_edges = [e for e in edges if e.relation_type == "file_import"]

    assert len(file_edges) >= 1
    for edge in file_edges:
        assert edge.source_file_id is not None
        assert edge.target_file_id is not None
