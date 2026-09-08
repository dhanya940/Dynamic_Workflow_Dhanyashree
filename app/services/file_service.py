"""File upload and download service for Task 5."""
import os
import uuid
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import BinaryIO

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.models.uploaded_file import UploadedFile
from app.core.config import settings

# Allowed file types per spec
ALLOWED_TYPES = {"pdf", "doc", "docx", "jpg", "jpeg", "png"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def validate_file(file: UploadFile) -> None:
    """Validate file type and size before upload."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_TYPES)}"
        )
    
    # Read file content to check size
    content = file.file.read()
    file.file.seek(0)  # Reset file pointer
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE / (1024*1024)} MB"
        )


def upload_file(db: Session, file: UploadFile) -> UploadedFile:
    """Upload file, validate it, and store metadata in database."""
    validate_file(file)
    
    # Generate unique filename
    ext = file.filename.split(".")[-1].lower()
    unique_id = secrets.token_urlsafe(8)
    stored_name = f"{unique_id}_{file.filename}"
    file_path = UPLOAD_DIR / stored_name
    
    # Save file to disk
    with open(file_path, "wb") as buffer:
        content = file.file.read()
        buffer.write(content)
    
    # Store metadata in database
    uploaded_file = UploadedFile(
        original_name=file.filename,
        stored_name=stored_name,
        file_path=str(file_path),
        file_size=len(content),
        uploaded_at=datetime.utcnow()
    )
    
    db.add(uploaded_file)
    db.commit()
    db.refresh(uploaded_file)
    
    return uploaded_file


def get_file(db: Session, file_id: uuid.UUID) -> UploadedFile:
    """Get file metadata by ID."""
    file = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file


def generate_download_token(file_id: uuid.UUID) -> str:
    """Generate a secure download token valid for 10 minutes."""
    expiry = datetime.utcnow() + timedelta(minutes=10)
    token_data = f"{file_id}:{expiry.timestamp()}:{secrets.token_urlsafe(16)}"
    return token_data


def validate_download_token(token: str) -> uuid.UUID | None:
    """Validate download token and return file_id if valid."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        
        file_id = uuid.UUID(parts[0])
        expiry_timestamp = float(parts[1])
        
        if datetime.utcnow() > datetime.fromtimestamp(expiry_timestamp):
            return None
        
        return file_id
    except (ValueError, IndexError):
        return None
