from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Metric(Base):
    __tablename__ = "metrics"

    version_id = Column(UUID(as_uuid=True), ForeignKey("project_versions.id"), primary_key=True)
    circular_dependencies = Column(Integer, default=0)
    avg_complexity = Column(Float, nullable=True)
    coupling_score = Column(Float, nullable=True)
    cohesion_score = Column(Float, nullable=True)
    dead_code_count = Column(Integer, default=0)

    version = relationship("ProjectVersion", back_populates="metrics")