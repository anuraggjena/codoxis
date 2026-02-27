import uuid
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ProjectVersion(Base):
    __tablename__ = "project_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    architecture_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="versions")
    files = relationship("File", back_populates="version", cascade="all, delete")
    edges = relationship("Edge", back_populates="version", cascade="all, delete")
    metrics = relationship("Metric", back_populates="version", uselist=False, cascade="all, delete")