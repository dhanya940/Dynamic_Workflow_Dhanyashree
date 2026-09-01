"""
submissions table — the parent record for each form submission.
Fields per spec: form_version_id, response_id, submitted_at,
completion_time_seconds.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_version_id = Column(UUID(as_uuid=True), ForeignKey("form_versions.id"), nullable=False)
    response_id = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)  # public-facing reference
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completion_time_seconds = Column(Integer, nullable=True)

    form_version = relationship("FormVersion", back_populates="submissions")
    response_values = relationship("ResponseValue", back_populates="submission", cascade="all, delete-orphan")
