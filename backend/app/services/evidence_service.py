"""
Evidence Service
================
Local-disk implementation for the prototype, behind a small interface so it
can be swapped for S3 / Azure Blob / GCS / SharePoint / Google Drive later
without touching routers or models.
"""
import hashlib
import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.config import settings

Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)


def validate_file(file: UploadFile, size_bytes: int):
    ext = Path(file.filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": f"File type {ext} not allowed", "error_code": "INVALID_FILE_TYPE"},
        )
    if size_bytes > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail={"success": False, "message": "File exceeds max upload size", "error_code": "FILE_TOO_LARGE"},
        )


def store_file(file: UploadFile, content: bytes) -> dict:
    """Persists to local disk. Returns metadata dict. Swap this function's
    body for a cloud SDK call to migrate storage backends."""
    ext = Path(file.filename).suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    storage_path = os.path.join(settings.UPLOAD_DIR, safe_name)
    with open(storage_path, "wb") as f:
        f.write(content)
    checksum = hashlib.sha256(content).hexdigest()
    return {
        "storage_path": storage_path,
        "checksum": checksum,
        "file_size": len(content),
    }
