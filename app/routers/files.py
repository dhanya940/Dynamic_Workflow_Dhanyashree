"""Task 5: File Upload and Download endpoints."""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.routers.auth import get_current_user
from app.schemas.file import FileUploadOut, FileDownloadOut
from app.services.file_service import (
    upload_file,
    get_file,
    generate_download_token,
    validate_download_token
)

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload", response_model=FileUploadOut, status_code=status.HTTP_201_CREATED)
def upload_file_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file (PDF, DOC, DOCX, JPG, PNG) with max size 5MB."""
    return upload_file(db, file)


@router.get("/{file_id}", response_model=FileDownloadOut)
def generate_download_link(
    file_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Generate a secure download URL valid for 10 minutes."""
    file = get_file(db, file_id)
    token = generate_download_token(file_id)
    return FileDownloadOut(
        file_id=file_id,
        download_url=f"/files/{file_id}/download?token={token}",
        expires_in_seconds=600
    )


@router.get("/{file_id}/download")
def download_file(
    file_id: uuid.UUID,
    token: str,
    db: Session = Depends(get_db)
):
    """Download file using secure token."""
    validated_file_id = validate_download_token(token)
    
    if not validated_file_id or validated_file_id != file_id:
        raise HTTPException(status_code=401, detail="Invalid or expired download token")
    
    file = get_file(db, file_id)
    
    if not Path(file.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file.file_path,
        filename=file.original_name,
        media_type="application/octet-stream"
    )
