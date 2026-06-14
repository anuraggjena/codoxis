"""
End-to-end API flow test mirroring the manual E2E validation checklist.
Uses the sample_repo fixture zipped in-memory.
"""
import io
import uuid
import zipfile
from pathlib import Path
from unittest.mock import patch

import pytest
from app.auth.utils import hash_password, create_access_token
from app.models.user import User


SAMPLE_REPO = Path(__file__).parent / "fixtures" / "sample_repo"


def _zip_sample_repo() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in SAMPLE_REPO.rglob("*"):
            if path.is_file():
                zf.write(path, path.relative_to(SAMPLE_REPO).as_posix())
    return buf.getvalue()


def _register_and_login(client, email: str | None = None, password: str = "testpass123"):
    email = email or f"e2e-{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 200, reg.text

    login = client.post("/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    return email, token


def test_full_e2e_flow(client, db):
    """Register → login → project → upload → dashboard → timeline → refactor → graph → auth checks."""
    with patch(
        "app.routers.ai.generate_ai_response",
        return_value="Focus on the highest-centrality file first.",
    ):
        _run_e2e_flow(client, db)


def _run_e2e_flow(client, db):
    email, token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    proj = client.post("/projects/", json={"name": "E2E Test Project"}, headers=headers)
    assert proj.status_code == 200, proj.text
    project_id = proj.json()["id"]

    # Upload ZIP
    zip_bytes = _zip_sample_repo()
    upload = client.post(
        f"/ingestion/upload/{project_id}",
        files={"file": ("sample_repo.zip", zip_bytes, "application/zip")},
        headers=headers,
    )
    assert upload.status_code == 200, upload.text
    upload_data = upload.json()
    assert "version_id" in upload_data
    assert upload_data.get("architecture_score") is not None
    version_id = upload_data["version_id"]

    # Dashboard
    dash = client.get(f"/analysis/dashboard/{version_id}", headers=headers)
    assert dash.status_code == 200, dash.text
    dashboard = dash.json()
    assert dashboard["version_info"]["version_id"] == version_id
    assert dashboard["metrics"]["total_files"] >= 1

    # Timeline
    timeline = client.get(f"/analysis/timeline/{project_id}", headers=headers)
    assert timeline.status_code == 200, timeline.text
    assert len(timeline.json()["timeline"]) >= 1

    # Graph
    graph = client.get(f"/analysis/graph/{version_id}", headers=headers)
    assert graph.status_code == 200, graph.text
    graph_data = graph.json()
    assert len(graph_data["nodes"]) >= 1

    # Refactor plan (rule engine; AI may be mocked or skipped)
    plan = client.get(f"/ai/refactor-plan/{version_id}?mode=beginner&limit=5", headers=headers)
    assert plan.status_code == 200, plan.text
    plan_data = plan.json()
    assert "recommendations" in plan_data
    assert "summary" in plan_data

    # AI Q&A
    ask = client.get(
        f"/ai/ask/{version_id}?question=Which+file+is+most+critical",
        headers=headers,
    )
    assert ask.status_code == 200, ask.text
    assert ask.json()["answer"]

    # Auth: no token → 401
    no_auth = client.get(f"/analysis/dashboard/{version_id}")
    assert no_auth.status_code == 401

    # Auth: wrong user → 403
    other = User(email=f"other-{uuid.uuid4().hex[:8]}@example.com", hashed_password=hash_password("x"))
    db.add(other)
    db.commit()
    other_token = create_access_token({"sub": str(other.id)})
    denied = client.get(
        f"/analysis/dashboard/{version_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert denied.status_code == 403

    # Second upload → version 2
    upload2 = client.post(
        f"/ingestion/upload/{project_id}",
        files={"file": ("sample_repo.zip", zip_bytes, "application/zip")},
        headers=headers,
    )
    assert upload2.status_code == 200, upload2.text
    assert upload2.json()["version_number"] == 2

    timeline2 = client.get(f"/analysis/timeline/{project_id}", headers=headers)
    assert len(timeline2.json()["timeline"]) == 2
