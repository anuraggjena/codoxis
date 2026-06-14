import logging
import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from app.database import get_db
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.ai_rate_limit import AIRateLimitMiddleware

# Routers
from app.auth.routes import router as auth_router
from app.routers.project import router as project_router
from app.routers.ingestion import router as ingestion_router
from app.routers.github_ingestion import router as github_ingestion_router
from app.routers.github_auth import router as github_auth_router
from app.routers.ai import router as ai_router
from app.routers.analysis import router as analysis_router


app = FastAPI(
    title="Codoxis Backend",
    description="AI-powered codebase architecture intelligence platform",
    version="1.0.0"
)

logging.basicConfig(level=logging.INFO)

app.add_middleware(AIRateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SECRET_KEY"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database schema is managed by Alembic migrations.
# Run `alembic upgrade head` before starting the server.


@app.get("/health")
def health(db: Session = Depends(get_db)):
    from sqlalchemy import text

    db.execute(text("SELECT 1"))
    alembic_version = None
    try:
        row = db.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).first()
        if row:
            alembic_version = row[0]
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "codoxis-backend",
        "alembic_version": alembic_version,
    }


@app.get("/")
def root():
    return {
        "message": "Codoxis backend running"
    }


# Register routers
app.include_router(auth_router)
app.include_router(project_router)
app.include_router(ingestion_router)
app.include_router(github_ingestion_router)
app.include_router(github_auth_router)
app.include_router(ai_router)
app.include_router(analysis_router)
