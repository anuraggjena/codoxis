import uuid
from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(UUID(as_uuid=True), ForeignKey("project_versions.id"), nullable=False)
    path = Column(String, nullable=False)
    language = Column(String, nullable=False)
    loc = Column(Integer, nullable=True)
    complexity_score = Column(Float, nullable=True)
    hash = Column(String, nullable=True)

    version = relationship("ProjectVersion", back_populates="files")
    symbols = relationship("Symbol", back_populates="file", cascade="all, delete")