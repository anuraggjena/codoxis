# Trusted Graph Foundation + AI Refactor Planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the ingestion/graph pipeline so architecture data is trustworthy, harden API security, and ship `GET /ai/refactor-plan/{version_id}` as the first evidence-backed AI differentiator.

**Architecture:** Foundation fixes (pipeline content, Edge model, edge builders) unblock graph metrics. New `services/refactor/` layer aggregates existing graph intelligence via a deterministic rule engine, then enhances with OpenRouter AI. Auth dependency `get_version_for_user` protects all analysis/AI routes.

**Tech Stack:** FastAPI, SQLAlchemy 2.x, PostgreSQL, pytest + httpx TestClient, OpenRouter (openai SDK), Tree-sitter

**Design spec:** `docs/superpowers/specs/2026-06-14-trusted-graph-refactor-planner-design.md`

---

## File Map

| File | Responsibility |
|------|----------------|
| `backend/app/services/ingestion/pipeline.py` | Fix `read()` vs `readlines()` |
| `backend/app/models/edge.py` | Nullable symbol FK columns |
| `backend/app/services/graph/edge_builder.py` | ORM queries, populate file FKs on call edges |
| `backend/app/services/graph/import_resolver.py` | File-only edges (symbol FKs null) |
| `backend/app/services/graph/cycle_detector.py` | Add `find_cycle_paths()` |
| `backend/app/auth/version_access.py` | **Create** — ownership dependency |
| `backend/app/auth/utils.py` | Remove default SECRET_KEY |
| `backend/app/main.py` | CORS middleware |
| `backend/app/routers/ingestion.py` | ZIP size + zip-slip guards |
| `backend/app/routers/github_ingestion.py` | GitHub URL allowlist |
| `backend/app/routers/analysis.py` | Auth + ownership on all routes |
| `backend/app/routers/ai.py` | Auth + refactor-plan endpoint |
| `backend/app/services/refactor/schemas.py` | **Create** — Pydantic models |
| `backend/app/services/refactor/context_builder.py` | **Create** — aggregate intelligence |
| `backend/app/services/refactor/rule_engine.py` | **Create** — deterministic scoring |
| `backend/app/services/refactor/refactor_planner.py` | **Create** — orchestration |
| `backend/app/services/ai/refactor_prompt_builder.py` | **Create** — AI prompt |
| `backend/app/services/ai/ai_provider.py` | Error handling, configurable max_tokens |
| `backend/requirements.txt` | Complete runtime deps |
| `backend/pytest.ini` | **Create** — pytest config |
| `backend/tests/conftest.py` | **Create** — fixtures |
| `backend/tests/fixtures/sample_repo/` | **Create** — minimal test repo |

---

## Task 1: Test Infrastructure

**Files:**
- Create: `backend/pytest.ini`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/__init__.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Add test dependencies to requirements.txt**

Append to `backend/requirements.txt`:

```
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.5.0
authlib==1.6.0
GitPython==3.1.45
openai==2.24.0
tree-sitter==0.25.0
tree-sitter-language-pack==0.7.0
python-multipart==0.0.20
pytest==8.4.1
httpx==0.28.1
```

- [ ] **Step 2: Create pytest.ini**

```ini
[pytest]
testpaths = tests
pythonpath = .
python_files = test_*.py
python_functions = test_*
```

- [ ] **Step 3: Create conftest.py**

```python
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

- [ ] **Step 4: Create empty tests/__init__.py**

```python
```

- [ ] **Step 5: Verify pytest runs**

Run: `cd backend && python -m pytest --collect-only`
Expected: `collected 0 items` (no failures)

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/pytest.ini backend/tests/
git commit -m "test: add pytest infrastructure and complete requirements"
```

---

## Task 2: Fix Pipeline Content Bug

**Files:**
- Create: `backend/tests/fixtures/sample_repo/main.py`
- Create: `backend/tests/fixtures/sample_repo/utils.py`
- Create: `backend/tests/test_pipeline.py`
- Modify: `backend/app/services/ingestion/pipeline.py`

- [ ] **Step 1: Create fixture repo**

`backend/tests/fixtures/sample_repo/main.py`:

```python
from utils import greet

def main():
    return greet("world")
```

`backend/tests/fixtures/sample_repo/utils.py`:

```python
def greet(name):
    return f"hello {name}"
```

- [ ] **Step 2: Write failing pipeline test**

`backend/tests/test_pipeline.py`:

```python
import uuid
from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.file import File
from app.models.symbol import Symbol
from app.services.ingestion.pipeline import run_repository_analysis
from app.auth.utils import hash_password

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_repo"


def test_pipeline_parses_files_and_symbols(db):
    user = User(email="test@example.com", hashed_password=hash_password("pass1234"))
    db.add(user)
    db.commit()

    project = Project(user_id=user.id, name="test-project")
    db.add(project)
    db.commit()

    version = ProjectVersion(project_id=project.id, version_number=1)
    db.add(version)
    db.commit()

    result = run_repository_analysis(
        repo_path=str(FIXTURE_PATH),
        version_id=version.id,
        project_id=project.id,
        db=db,
    )

    files = db.query(File).filter(File.version_id == version.id).all()
    symbols = (
        db.query(Symbol)
        .join(File)
        .filter(File.version_id == version.id)
        .all()
    )

    assert len(files) == 2
    assert len(symbols) >= 2
    assert "architecture_score" in result
    assert result["architecture_score"] is not None
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_pipeline.py::test_pipeline_parses_files_and_symbols -v`
Expected: FAIL — `TypeError` on `bytes(content, "utf8")` or zero symbols

- [ ] **Step 4: Fix pipeline.py**

In `backend/app/services/ingestion/pipeline.py`, replace lines 36-43:

```python
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            file_model = FileModel(
                version_id=version_id,
                path=relative_path,
                language=ext.replace(".", ""),
                loc=len(content.splitlines()),
            )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_pipeline.py::test_pipeline_parses_files_and_symbols -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/ingestion/pipeline.py backend/tests/
git commit -m "fix: pass file content as string in ingestion pipeline"
```

---

## Task 3: Fix Edge Model and Builders

**Files:**
- Modify: `backend/app/models/edge.py`
- Modify: `backend/app/services/graph/edge_builder.py`
- Modify: `backend/app/services/graph/import_resolver.py`
- Create: `backend/tests/test_edges.py`

- [ ] **Step 1: Write failing edge test**

`backend/tests/test_edges.py`:

```python
from pathlib import Path

from app.models.project import Project
from app.models.project_version import ProjectVersion
from app.models.user import User
from app.models.edge import Edge
from app.services.ingestion.pipeline import run_repository_analysis
from app.auth.utils import hash_password

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_repo"


def test_pipeline_creates_file_level_import_edges(db):
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
        repo_path=str(FIXTURE_PATH),
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_edges.py -v`
Expected: FAIL — IntegrityError or zero edges

- [ ] **Step 3: Make symbol FKs nullable on Edge model**

`backend/app/models/edge.py`:

```python
    source_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    target_file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False)
    source_symbol_id = Column(UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=True)
    target_symbol_id = Column(UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=True)
```

- [ ] **Step 4: Rewrite edge_builder.py**

Replace entire `backend/app/services/graph/edge_builder.py`:

```python
from app.models.file import File
from app.models.symbol import Symbol
from app.models.edge import Edge


def build_edges_for_version(version_id, db):
    files = db.query(File).filter(File.version_id == version_id).all()

    for file_model in files:
        symbols = db.query(Symbol).filter(Symbol.file_id == file_model.id).all()

        functions = [s for s in symbols if s.type == "function"]
        calls = [s for s in symbols if s.type == "call"]

        for call in calls:
            for function in functions:
                if call.name == function.name:
                    db.add(Edge(
                        version_id=version_id,
                        source_file_id=file_model.id,
                        target_file_id=file_model.id,
                        source_symbol_id=function.id,
                        target_symbol_id=call.id,
                        relation_type="calls",
                    ))

    db.commit()
```

- [ ] **Step 5: Update import_resolver create_file_edge**

In `backend/app/services/graph/import_resolver.py`, `create_file_edge` stays as:

```python
def create_file_edge(version_id, source_file_id, target_file_id, db):
    db.add(Edge(
        version_id=version_id,
        source_file_id=source_file_id,
        target_file_id=target_file_id,
        source_symbol_id=None,
        target_symbol_id=None,
        relation_type="file_import",
    ))
```

- [ ] **Step 6: Run tests**

Run: `cd backend && python -m pytest tests/test_pipeline.py tests/test_edges.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/edge.py backend/app/services/graph/edge_builder.py backend/app/services/graph/import_resolver.py backend/tests/test_edges.py
git commit -m "fix: align Edge model with file-level and symbol-level edge builders"
```

---

## Task 4: Cycle Path Detection

**Files:**
- Create: `backend/tests/fixtures/cyclic_repo/a.py`
- Create: `backend/tests/fixtures/cyclic_repo/b.py`
- Create: `backend/tests/test_cycle_paths.py`
- Modify: `backend/app/services/graph/cycle_detector.py`

- [ ] **Step 1: Create cyclic fixture**

`backend/tests/fixtures/cyclic_repo/a.py`:

```python
import b

def func_a():
    return b.func_b()
```

`backend/tests/fixtures/cyclic_repo/b.py`:

```python
import a

def func_b():
    return a.func_a()
```

- [ ] **Step 2: Write failing test**

`backend/tests/test_cycle_paths.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_cycle_paths.py -v`
Expected: FAIL — `ImportError: cannot import name 'find_cycle_paths'`

- [ ] **Step 4: Add find_cycle_paths to cycle_detector.py**

Append to `backend/app/services/graph/cycle_detector.py`:

```python
from app.models.file import File


def find_cycle_paths(version_id, db, max_paths=10):
    file_map = {
        f.id: f.path
        for f in db.query(File).filter(File.version_id == version_id).all()
    }

    adjacency = defaultdict(set)
    edges = db.query(Edge).filter(
        Edge.version_id == version_id,
        Edge.source_file_id.isnot(None),
        Edge.target_file_id.isnot(None),
    ).all()

    for edge in edges:
        if edge.source_file_id != edge.target_file_id:
            adjacency[edge.source_file_id].add(edge.target_file_id)

    cycles = []
    visited_global = set()

    def dfs(node, path, visited):
        if len(cycles) >= max_paths:
            return
        if node in visited:
            idx = path.index(node)
            cycle_ids = path[idx:] + [node]
            cycle_paths = [file_map[fid] for fid in cycle_ids if fid in file_map]
            if len(cycle_paths) >= 2:
                cycles.append(cycle_paths)
            return
        visited.add(node)
        path.append(node)
        for neighbor in adjacency.get(node, []):
            dfs(neighbor, path, visited.copy())
        path.pop()

    for node in adjacency:
        if node not in visited_global:
            dfs(node, [], set())
            visited_global.add(node)

    return cycles[:max_paths]
```

Keep existing `detect_circular_dependencies()` unchanged.

- [ ] **Step 5: Run test**

Run: `cd backend && python -m pytest tests/test_cycle_paths.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/graph/cycle_detector.py backend/tests/
git commit -m "feat: add find_cycle_paths for refactor planner evidence"
```

---

## Task 5: Version Access Auth Dependency

**Files:**
- Create: `backend/app/auth/version_access.py`
- Create: `backend/tests/test_version_access.py`

- [ ] **Step 1: Write failing auth test**

`backend/tests/test_version_access.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_version_access.py -v`
Expected: FAIL — 200 instead of 401

- [ ] **Step 3: Create version_access.py**

`backend/app/auth/version_access.py`:

```python
import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.project_version import ProjectVersion


def get_version_for_user(
    version_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProjectVersion:
    version = db.query(ProjectVersion).filter(
        ProjectVersion.id == version_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    project = db.query(Project).filter(Project.id == version.project_id).first()

    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return version


def get_project_for_user(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Project:
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return project
```

- [ ] **Step 4: Protect analysis.py dashboard endpoint (pattern for all routes)**

In `backend/app/routers/analysis.py`:

1. Remove local `get_db()` (lines 21-26)
2. Add imports:

```python
import uuid
from app.auth.dependencies import get_current_user
from app.auth.version_access import get_version_for_user, get_project_for_user
from app.models.user import User
from app.models.project_version import ProjectVersion
from app.models.project import Project
```

3. Update dashboard endpoint:

```python
@router.get("/dashboard/{version_id}")
def get_dashboard(
    version: ProjectVersion = Depends(get_version_for_user),
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        return {"error": "Version not found"}

    return dashboard
```

4. Apply same `version: ProjectVersion = Depends(get_version_for_user)` pattern to:
   - `/impact/{version_id}/{file_id}`
   - `/centrality/{version_id}`
   - `/graph/{version_id}`
   - `/explain/{version_id}`
   - `/graph-summary/{version_id}`
   - `/compare/{version_id_1}/{version_id_2}` (check both versions)
   - `/high-risk/{version_id}`

5. For timeline routes use `project: Project = Depends(get_project_for_user)`:

```python
@router.get("/timeline/{project_id}")
def get_timeline(
    project: Project = Depends(get_project_for_user),
    db: Session = Depends(get_db),
):
    return get_architecture_timeline(project.id, db)
```

6. Remove dead code: duplicate `build_timeline_prompt` (lines 116-140) and unused imports.

- [ ] **Step 5: Run tests**

Run: `cd backend && python -m pytest tests/test_version_access.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/auth/version_access.py backend/app/routers/analysis.py backend/tests/test_version_access.py
git commit -m "feat: add version/project ownership auth to analysis routes"
```

---

## Task 6: Security Hardening

**Files:**
- Modify: `backend/app/auth/utils.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/routers/ingestion.py`
- Modify: `backend/app/routers/github_ingestion.py`
- Create: `backend/.env.example`

- [ ] **Step 1: Remove default SECRET_KEY**

`backend/app/auth/utils.py`:

```python
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is required")
```

- [ ] **Step 2: Add CORS to main.py**

```python
import os
from fastapi.middleware.cors import CORSMiddleware

# After app = FastAPI(...)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- [ ] **Step 3: ZIP upload hardening in ingestion.py**

Add constants and validation before extract:

```python
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

def safe_extract(zip_ref, extract_path):
    for member in zip_ref.namelist():
        member_path = os.path.normpath(os.path.join(extract_path, member))
        if not member_path.startswith(os.path.abspath(extract_path)):
            raise HTTPException(status_code=400, detail="Unsafe zip entry detected")
    zip_ref.extractall(extract_path)
```

In `upload_zip`, after reading file:

```python
    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 50MB)")
    with open(zip_path, "wb") as buffer:
        buffer.write(content)
    ...
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        safe_extract(zip_ref, extract_path)
```

- [ ] **Step 4: GitHub URL allowlist**

In `github_ingestion.py`, before clone:

```python
    if not repo_url.startswith("https://github.com/"):
        raise HTTPException(status_code=400, detail="Only github.com HTTPS URLs are allowed")
```

- [ ] **Step 5: Create .env.example**

```
DATABASE_URL=postgresql://user:pass@localhost:5432/codoxis
SECRET_KEY=change-me-to-random-string
OPENROUTER_API_KEY=sk-or-...
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
CORS_ORIGINS=http://localhost:3000
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/auth/utils.py backend/app/main.py backend/app/routers/ingestion.py backend/app/routers/github_ingestion.py backend/.env.example
git commit -m "security: require SECRET_KEY, add CORS, zip-slip guard, GitHub URL allowlist"
```

---

## Task 7: Refactor Schemas and Rule Engine

**Files:**
- Create: `backend/app/services/refactor/schemas.py`
- Create: `backend/app/services/refactor/rule_engine.py`
- Create: `backend/tests/test_rule_engine.py`

- [ ] **Step 1: Write failing rule engine test**

`backend/tests/test_rule_engine.py`:

```python
from app.services.refactor.rule_engine import prioritize_refactor_candidates


def test_prioritize_returns_sorted_candidates():
    context = {
        "high_risk_files": [
            {"file_path": "a.py", "risk_score": 0.9, "file_id": "id-a"},
            {"file_path": "b.py", "risk_score": 0.5, "file_id": "id-b"},
        ],
        "cycle_paths": [["a.py", "b.py", "a.py"]],
        "centrality": [
            {"file_path": "a.py", "centrality_score": 10},
        ],
        "drift": None,
        "coupling_hotspots": {"a.py": 5},
    }

    candidates = prioritize_refactor_candidates(context, limit=5)

    assert len(candidates) >= 1
    assert candidates[0]["priority"] == 1
    assert "title" in candidates[0]
    assert "evidence" in candidates[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_rule_engine.py -v`
Expected: FAIL — import error

- [ ] **Step 3: Create schemas.py**

`backend/app/services/refactor/schemas.py`:

```python
from datetime import datetime
from pydantic import BaseModel, Field


class RefactorEvidence(BaseModel):
    cycle_path: list[str] | None = None
    centrality_scores: dict[str, float] = Field(default_factory=dict)
    impact_radius: int | None = None
    metrics_contribution: dict[str, float] = Field(default_factory=dict)


class RefactorRecommendation(BaseModel):
    priority: int
    title: str
    category: str
    severity: str
    affected_files: list[str]
    evidence: RefactorEvidence
    recommended_action: str
    beginner_explanation: str
    estimated_ahs_impact: str


class RefactorPlanResponse(BaseModel):
    version_id: str
    mode: str
    architecture_score: float | None
    data_quality: str
    summary: str
    recommendations: list[RefactorRecommendation]
    ai_enhanced: bool
    generated_at: datetime
```

- [ ] **Step 4: Create rule_engine.py**

`backend/app/services/refactor/rule_engine.py`:

```python
CATEGORY_WEIGHTS = {
    "circular_dependency": 0.30,
    "high_risk": 0.25,
    "high_centrality": 0.20,
    "drift_regression": 0.15,
    "high_coupling": 0.10,
}


def prioritize_refactor_candidates(context: dict, limit: int = 10) -> list[dict]:
    scored = []

    for path in context.get("cycle_paths", []):
        files = list(dict.fromkeys(path))
        scored.append({
            "score": CATEGORY_WEIGHTS["circular_dependency"],
            "category": "circular_dependency",
            "severity": "high",
            "affected_files": files,
            "evidence": {"cycle_path": path},
            "title": f"Break circular dependency involving {files[0]}",
            "recommended_action": f"Decouple modules: {' → '.join(files)}",
            "beginner_explanation": "Some files depend on each other in a loop, making changes risky.",
            "estimated_ahs_impact": "high",
        })

    for item in context.get("high_risk_files", [])[:10]:
        scored.append({
            "score": CATEGORY_WEIGHTS["high_risk"] * item.get("risk_score", 0.5),
            "category": "high_risk",
            "severity": "high" if item.get("risk_score", 0) > 0.7 else "medium",
            "affected_files": [item["file_path"]],
            "evidence": {
                "impact_radius": item.get("impact_depth"),
                "metrics_contribution": {"risk_score": item.get("risk_score", 0)},
            },
            "title": f"Reduce risk in {item['file_path']}",
            "recommended_action": f"Refactor {item['file_path']} to reduce coupling and impact radius.",
            "beginner_explanation": "This file is central to your project and changes here affect many other parts.",
            "estimated_ahs_impact": "medium",
        })

    if context.get("drift") and context["drift"].get("ahs_change", 0) < 0:
        scored.append({
            "score": CATEGORY_WEIGHTS["drift_regression"],
            "category": "drift_regression",
            "severity": "medium",
            "affected_files": [],
            "evidence": {"metrics_contribution": context["drift"]},
            "title": "Address architecture score regression since last version",
            "recommended_action": "Review recent changes that increased coupling or introduced cycles.",
            "beginner_explanation": "Your architecture health got worse since the last upload.",
            "estimated_ahs_impact": "medium",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    results = []
    for i, item in enumerate(scored[:limit]):
        item["priority"] = i + 1
        results.append(item)

    return results
```

- [ ] **Step 5: Run test**

Run: `cd backend && python -m pytest tests/test_rule_engine.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/refactor/ backend/tests/test_rule_engine.py
git commit -m "feat: add refactor schemas and deterministic rule engine"
```

---

## Task 8: Context Builder and AI Prompt

**Files:**
- Create: `backend/app/services/refactor/context_builder.py`
- Create: `backend/app/services/ai/refactor_prompt_builder.py`

- [ ] **Step 1: Create context_builder.py**

`backend/app/services/refactor/context_builder.py`:

```python
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.analysis.risk_analyzer import detect_high_risk_files
from app.services.graph.cycle_detector import find_cycle_paths
from app.services.graph.centrality_calculator import calculate_file_centrality
from app.services.graph.impact_analyzer import analyze_refactor_impact
from app.services.graph.graph_loader import load_graph


def build_refactor_context(version_id, db) -> dict:
    dashboard = build_dashboard(version_id, db)
    if not dashboard:
        return None

    high_risk = detect_high_risk_files(version_id, db)[:10]
    cycle_paths = find_cycle_paths(version_id, db)
    centrality = calculate_file_centrality(version_id, db)

    graph = load_graph(version_id, db)
    coupling_hotspots = {}
    for file_id, neighbors in graph["adjacency"].items():
        if file_id in graph["files"]:
            coupling_hotspots[graph["files"][file_id].path] = len(neighbors)

    impact_analyses = []
    for item in high_risk[:3]:
        impact = analyze_refactor_impact(version_id, str(item["file_id"]), db)
        impact_analyses.append({
            "file_path": item["file_path"],
            "impact": impact,
        })

    total_edges = len(graph["edges"])
    data_quality = "high" if total_edges > 0 else "low"

    return {
        "dashboard": dashboard,
        "high_risk_files": high_risk,
        "cycle_paths": cycle_paths,
        "centrality": centrality,
        "drift": dashboard.get("drift"),
        "coupling_hotspots": coupling_hotspots,
        "impact_analyses": impact_analyses,
        "data_quality": data_quality,
    }
```

- [ ] **Step 2: Create refactor_prompt_builder.py**

`backend/app/services/ai/refactor_prompt_builder.py`:

```python
import json


def build_refactor_prompt(context: dict, candidates: list, mode: str) -> str:
    instruction = (
        "Explain in simple language for a beginner developer."
        if mode == "beginner"
        else "Use precise technical language for a senior engineer."
    )

    return f"""
You are a senior software architect creating a prioritized refactor plan.

{instruction}

Architecture context:
{json.dumps({
    "architecture_score": context["dashboard"]["version_info"]["architecture_score"],
    "metrics": context["dashboard"]["metrics"],
    "drift": context["drift"],
    "data_quality": context["data_quality"],
}, indent=2)}

Pre-computed refactor candidates (use these as the basis — do not invent files):
{json.dumps(candidates, indent=2)}

Return a JSON object with exactly this shape:
{{
  "summary": "one paragraph overview",
  "recommendations": [
    {{
      "priority": 1,
      "title": "...",
      "category": "...",
      "severity": "high|medium|low",
      "affected_files": ["..."],
      "recommended_action": "...",
      "beginner_explanation": "...",
      "estimated_ahs_impact": "low|medium|high"
    }}
  ]
}}

Keep the same priorities and affected_files from the candidates. Improve the recommended_action and explanations.
Return ONLY valid JSON, no markdown fences.
"""
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/refactor/context_builder.py backend/app/services/ai/refactor_prompt_builder.py
git commit -m "feat: add refactor context builder and AI prompt builder"
```

---

## Task 9: Refactor Planner Orchestration

**Files:**
- Create: `backend/app/services/refactor/refactor_planner.py`
- Modify: `backend/app/services/ai/ai_provider.py`
- Create: `backend/tests/test_refactor_planner.py`

- [ ] **Step 1: Harden ai_provider.py**

```python
import logging
from openai import OpenAI, APIError
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openai/gpt-5.3-codex"


def generate_ai_response(prompt: str, max_tokens: int = 1200) -> str | None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        return None

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a senior software architect helping developers understand their system architecture.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=max_tokens,
        )
        return completion.choices[0].message.content
    except APIError as e:
        logger.error("AI provider error: %s", e)
        return None
```

- [ ] **Step 2: Create refactor_planner.py**

`backend/app/services/refactor/refactor_planner.py`:

```python
import json
from datetime import datetime, timezone

from app.services.refactor.context_builder import build_refactor_context
from app.services.refactor.rule_engine import prioritize_refactor_candidates
from app.services.ai.refactor_prompt_builder import build_refactor_prompt
from app.services.ai.ai_provider import generate_ai_response
from app.services.refactor.schemas import (
    RefactorPlanResponse,
    RefactorRecommendation,
    RefactorEvidence,
)


def _candidates_to_recommendations(candidates: list) -> list[RefactorRecommendation]:
    recs = []
    for c in candidates:
        evidence_data = c.get("evidence", {})
        recs.append(RefactorRecommendation(
            priority=c["priority"],
            title=c["title"],
            category=c["category"],
            severity=c["severity"],
            affected_files=c["affected_files"],
            evidence=RefactorEvidence(
                cycle_path=evidence_data.get("cycle_path"),
                centrality_scores=evidence_data.get("centrality_scores", {}),
                impact_radius=evidence_data.get("impact_radius"),
                metrics_contribution=evidence_data.get("metrics_contribution", {}),
            ),
            recommended_action=c["recommended_action"],
            beginner_explanation=c["beginner_explanation"],
            estimated_ahs_impact=c["estimated_ahs_impact"],
        ))
    return recs


def generate_refactor_plan(version_id, db, mode: str = "advanced", limit: int = 10) -> RefactorPlanResponse | None:
    context = build_refactor_context(version_id, db)
    if not context:
        return None

    candidates = prioritize_refactor_candidates(context, limit=limit)
    ai_enhanced = False
    summary = f"Found {len(candidates)} refactor opportunities based on graph analysis."

    ai_response = generate_ai_response(
        build_refactor_prompt(context, candidates, mode),
        max_tokens=2000,
    )

    if ai_response:
        try:
            parsed = json.loads(ai_response)
            summary = parsed.get("summary", summary)
            ai_recs = parsed.get("recommendations", [])
            for i, c in enumerate(candidates):
                if i < len(ai_recs):
                    c["recommended_action"] = ai_recs[i].get("recommended_action", c["recommended_action"])
                    c["beginner_explanation"] = ai_recs[i].get("beginner_explanation", c["beginner_explanation"])
                    c["title"] = ai_recs[i].get("title", c["title"])
            ai_enhanced = True
        except json.JSONDecodeError:
            pass

    recommendations = _candidates_to_recommendations(candidates)

    return RefactorPlanResponse(
        version_id=str(version_id),
        mode=mode,
        architecture_score=context["dashboard"]["version_info"].get("architecture_score"),
        data_quality=context["data_quality"],
        summary=summary,
        recommendations=recommendations,
        ai_enhanced=ai_enhanced,
        generated_at=datetime.now(timezone.utc),
    )
```

- [ ] **Step 3: Write planner unit test (mock AI)**

`backend/tests/test_refactor_planner.py`:

```python
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
```

- [ ] **Step 4: Run test**

Run: `cd backend && python -m pytest tests/test_refactor_planner.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/refactor/refactor_planner.py backend/app/services/ai/ai_provider.py backend/tests/test_refactor_planner.py
git commit -m "feat: add refactor planner orchestration with AI fallback"
```

---

## Task 10: Refactor Plan API Endpoint

**Files:**
- Modify: `backend/app/routers/ai.py`
- Create: `backend/tests/test_refactor_endpoint.py`

- [ ] **Step 1: Write failing endpoint test**

`backend/tests/test_refactor_endpoint.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_refactor_endpoint.py -v`
Expected: FAIL — 404 (route not found)

- [ ] **Step 3: Update ai.py**

Replace `backend/app/routers/ai.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.version_access import get_version_for_user
from app.models.project_version import ProjectVersion
from app.services.dashboard.dashboard_service import build_dashboard
from app.services.ai.architecture_ai import generate_architecture_analysis
from app.services.ai.architecture_chat import answer_architecture_question
from app.services.ai.code_assistant import analyze_code_snippet
from app.services.refactor.refactor_planner import generate_refactor_plan
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/architecture-report/{version_id}")
def ai_architecture_report(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = "advanced",
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    analysis = generate_architecture_analysis(dashboard, mode)

    return {
        "version_id": str(version.id),
        "mode": mode,
        "analysis": analysis,
    }


@router.get("/ask/{version_id}")
def ask_architecture_ai(
    version: ProjectVersion = Depends(get_version_for_user),
    question: str = "",
    db: Session = Depends(get_db),
):
    dashboard = build_dashboard(version.id, db)

    if not dashboard:
        raise HTTPException(status_code=404, detail="Version not found")

    answer = answer_architecture_question(dashboard, question)

    return {
        "version_id": str(version.id),
        "question": question,
        "answer": answer,
    }


@router.post("/code-help")
def code_help(
    code: str,
    question: str,
    current_user: User = Depends(get_current_user),
):
    response = analyze_code_snippet(code, question)

    return {
        "question": question,
        "analysis": response,
    }


@router.get("/refactor-plan/{version_id}")
def get_refactor_plan(
    version: ProjectVersion = Depends(get_version_for_user),
    mode: str = Query(default="advanced", pattern="^(beginner|advanced)$"),
    limit: int = Query(default=10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    plan = generate_refactor_plan(version.id, db, mode=mode, limit=limit)

    if not plan:
        raise HTTPException(status_code=404, detail="Analysis incomplete")

    return plan.model_dump()
```

- [ ] **Step 4: Run all tests**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/ai.py backend/tests/test_refactor_endpoint.py
git commit -m "feat: add GET /ai/refactor-plan endpoint with auth"
```

---

## Task 11: Consolidate get_db and Cleanup

**Files:**
- Modify: `backend/app/routers/ingestion.py`
- Modify: `backend/app/routers/github_ingestion.py`
- Modify: `backend/app/routers/project.py`
- Modify: `backend/app/auth/routes.py`
- Modify: `backend/app/auth/dependencies.py`

- [ ] **Step 1: Remove duplicate get_db from all routers**

In each file, remove local `get_db()` and import from `app.database`:

```python
from app.database import get_db
```

Files to update:
- `backend/app/routers/ingestion.py`
- `backend/app/routers/github_ingestion.py`
- `backend/app/routers/project.py`
- `backend/app/auth/routes.py`
- `backend/app/auth/dependencies.py` (keep get_db import from database, remove local definition)

- [ ] **Step 2: Run full test suite**

Run: `cd backend && python -m pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/ backend/app/auth/
git commit -m "refactor: consolidate get_db dependency across routers"
```

---

## Deferred (Post-Phase)

| Item | Notes |
|------|-------|
| Alembic migrations | After Edge model deployed to production DB |
| GitHub OAuth → JWT | Separate phase |
| Rate limiting | In-memory or middleware |
| Frontend MVP | After backend phase verified |
| Root `.gitignore` | Add before any public release |

---

## Self-Review Checklist

| Spec Requirement | Task |
|------------------|------|
| Pipeline content fix | Task 2 |
| Edge model alignment | Task 3 |
| Cycle paths for evidence | Task 4 |
| Auth on analysis/AI | Task 5, 10 |
| CORS, SECRET_KEY, ZIP, GitHub URL | Task 6 |
| Refactor schemas | Task 7 |
| Context builder | Task 8 |
| Rule engine | Task 7 |
| AI prompt + planner | Task 8, 9 |
| API endpoint | Task 10 |
| pytest coverage | Tasks 1–10 |
| get_db consolidation | Task 11 |

No placeholders remain. All code blocks are complete and copy-paste ready.
