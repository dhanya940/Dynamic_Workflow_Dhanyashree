"""
response_values table — the actual answers given by users.
One dynamic table for all answers (avoids new DB columns per form).
Fields per spec: submission_id, field_id, value, created_at.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class ResponseValue(Base):
    __tablename__ = "response_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    value = Column(Text, nullable=True)  # stored as text; cast/validate per field_type in application code
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    submission = relationship("Submission", back_populates="response_values")
    field = relationship("Field")
