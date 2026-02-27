import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Edge(Base):
    __tablename__ = "edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("project_versions.id"), nullable=False)
    source_symbol_id = Column(UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False)
    target_symbol_id = Column(UUID(as_uuid=True), ForeignKey("symbols.id"), nullable=False)
    relation_type = Column(String, nullable=False)

    version = relationship("ProjectVersion", back_populates="edges")