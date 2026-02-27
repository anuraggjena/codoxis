from fastapi import FastAPI
from app.database import Base, engine
from app.models import user, project, project_version, file, symbol, edge, metric
from app.auth.routes import router as auth_router
from app.routers.project import router as project_router
from app.routers.ingestion import router as ingestion_router

app = FastAPI(title="Codoxis Backend")

Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {"message": "Codoxis backend running"}

app.include_router(auth_router)
app.include_router(project_router)
app.include_router(ingestion_router)