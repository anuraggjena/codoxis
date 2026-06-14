import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("OPENROUTER_API_KEY", "test-key")

USE_POSTGRES = os.environ.get("PYTEST_USE_POSTGRES") == "1"
DATABASE_URL = (
    os.environ["DATABASE_URL"]
    if USE_POSTGRES and os.environ.get("DATABASE_URL", "").startswith("postgresql")
    else "sqlite:///:memory:"
)

from app.database import Base, get_db
from app.main import app
from app.models import oauth_token  # noqa: F401 — register table for create_all

if USE_POSTGRES:
    engine = create_engine(DATABASE_URL)
else:
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def _truncate_tables():
    tables = [
        "oauth_tokens", "metrics", "edges", "symbols", "files",
        "project_versions", "projects", "users",
    ]
    with engine.begin() as conn:
        for table in tables:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception:
                pass


@pytest.fixture(autouse=True)
def setup_db():
    if USE_POSTGRES:
        yield
        _truncate_tables()
    else:
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
from pathlib import Path


@pytest.fixture
def sample_repo():
    return Path(__file__).parent / "fixtures" / "sample_repo"
