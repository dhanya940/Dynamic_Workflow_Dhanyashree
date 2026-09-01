"""
form_share_links table — Task 6: shareable public links.
Not one of the tables listed in Task 2's schema, but the extra table needed
to satisfy "Generate Public Form Link" / "Store access token/slug" from
Task 6 without bolting a slug column onto forms itself (a form can get a
new link each time it's re-published to a new version).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.session import Base


class FormShareLink(Base):
    __tablename__ = "form_share_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    form_version_id = Column(UUID(as_uuid=True), ForeignKey("form_versions.id"), nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    form_version = relationship("FormVersion")
