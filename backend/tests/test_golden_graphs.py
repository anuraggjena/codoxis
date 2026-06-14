"""Golden graph fixture tests — assert stable graph metrics on sample_repo."""
import uuid
import json
from pathlib import Path

import pytest

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.file import File
from app.models.edge import Edge
from app.auth.utils import hash_password
from app.services.ingestion.pipeline import run_repository_analysis

SAMPLE_REPO = Path(__file__).parent / "fixtures" / "sample_repo"
GOLDEN = Path(__file__).parent / "golden" / "sample_repo.graph.json"


@pytest.fixture
def golden_spec():
    return json.loads(GOLDEN.read_text())


def test_sample_repo_golden_graph(db, golden_spec):
    user = User(email="golden@test.com", hashed_password=hash_password("pass"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="Golden Test")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    run_repository_analysis(str(SAMPLE_REPO), version.id, project.id, db)

    files = db.query(File).filter(File.version_id == version.id).all()
    paths = sorted(f.path.replace("\\", "/") for f in files)
    assert len(files) == golden_spec["file_count"]
    assert paths == sorted(golden_spec["file_paths"])

    import_edges = db.query(Edge).filter(
        Edge.version_id == version.id,
        Edge.relation_type == "file_import",
    ).all()
    assert len(import_edges) >= golden_spec["min_file_import_edges"]

    file_by_id = {f.id: f.path.replace("\\", "/") for f in files}
    spec = golden_spec["expected_import_edge"]
    found = any(
        spec["source_contains"] in file_by_id.get(e.source_file_id, "")
        and spec["target_contains"] in file_by_id.get(e.target_file_id, "")
        for e in import_edges
    )
    assert found, "Expected main.py → utils.py import edge"
