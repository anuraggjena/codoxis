from fastapi import FastAPI

from app.database import Base, engine

# Models (required for SQLAlchemy table creation)
from app.models import (
    user,
    project,
    project_version,
    file,
    symbol,
    edge,
    metric
)

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

# Create tables
Base.metadata.create_all(bind=engine)


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