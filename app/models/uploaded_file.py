"""
uploaded_files table — stores metadata for uploaded files (resumes, certificates, documents, images).
Fields per spec: id, original_name, stored_name, file_path, file_size, uploaded_at.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.database.session import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    original_name = Column(String, nullable=False)
    stored_name = Column(String, nullable=False, unique=True)
    file_path = Column(String, nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
