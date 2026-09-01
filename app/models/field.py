"""
fields table — questions/inputs belonging to a form version.
Fields per spec: id, form_version_id, label, field_type, placeholder,
is_required, display_order, validation_config.
"""
import uuid

from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.database.session import Base


class Field(Base):
    __tablename__ = "fields"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_version_id = Column(UUID(as_uuid=True), ForeignKey("form_versions.id"), nullable=False)
    label = Column(String, nullable=False)
    field_type = Column(String, nullable=False)  # text, email, date, dropdown, checkbox, file, etc.
    placeholder = Column(String, nullable=True)
    is_required = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, nullable=False, default=0)
    validation_config = Column(JSONB, nullable=True)  # e.g. {"min": 0, "max": 100}

    form_version = relationship("FormVersion", back_populates="fields")
    options = relationship("FieldOption", back_populates="field", cascade="all, delete-orphan")
    trigger_rules = relationship("ConditionalRule", foreign_keys="ConditionalRule.trigger_field_id",
                                  cascade="all, delete-orphan", passive_deletes=True)
    target_rules = relationship("ConditionalRule", foreign_keys="ConditionalRule.target_field_id",
                                cascade="all, delete-orphan", passive_deletes=True)
