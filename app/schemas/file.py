"""Pydantic schemas for file upload and download."""
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FileUploadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    original_name: str
    stored_name: str
    file_path: str
    file_size: int
    uploaded_at: datetime


class FileDownloadOut(BaseModel):
    file_id: uuid.UUID
    download_url: str
    expires_in_seconds: int
