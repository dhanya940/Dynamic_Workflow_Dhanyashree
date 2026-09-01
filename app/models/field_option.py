"""
field_options table — dropdown/checkbox choices for a field.
Fields per spec: id, field_id, option_label, option_value, display_order.
"""
import uuid

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class FieldOption(Base):
    __tablename__ = "field_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    field_id = Column(UUID(as_uuid=True), ForeignKey("fields.id"), nullable=False)
    option_label = Column(String, nullable=False)   # e.g. "Male" (shown to user)
    option_value = Column(String, nullable=False)   # e.g. "male" (stored value)
    display_order = Column(Integer, nullable=False, default=0)

    field = relationship("Field", back_populates="options")
