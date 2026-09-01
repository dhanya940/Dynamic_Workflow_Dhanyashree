"""
conditional_rules table — show/hide logic for dynamic forms.
Example: Experience = Yes -> show "Years of Experience".
Fields per spec: trigger_field_id, operator, comparison_value,
target_field_id, action.
"""
import uuid

from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class ConditionalRule(Base):
    __tablename__ = "conditional_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trigger_field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    operator = Column(String, nullable=False)            # e.g. "equals", "not_equals", "contains"
    comparison_value = Column(String, nullable=False)    # e.g. "Yes"
    target_field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    action = Column(String, nullable=False)               # e.g. "show", "hide"

    trigger_field = relationship("Field", foreign_keys=[trigger_field_id])
    target_field = relationship("Field", foreign_keys=[target_field_id])
