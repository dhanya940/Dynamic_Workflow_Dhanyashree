"""
form_versions table — published snapshots of a form.
Once published, existing responses always refer to this exact version;
future edits create a new version instead of mutating this one.
Fields per spec: id, form_id, version_number, is_active, published_at.
"""
import uuid

from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class FormVersion(Base):
    __tablename__ = "form_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_id = Column(UUID(as_uuid=True), ForeignKey("forms.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)

    form = relationship("Form", back_populates="versions")
    fields = relationship("Field", back_populates="form_version", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="form_version")
