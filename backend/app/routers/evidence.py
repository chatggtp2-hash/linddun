import uuid
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.permissions import require_any
from app.models.evidence import Evidence
from app.models.user import User
from app.schemas.evidence import EvidenceOut
from app.services.evidence_service import validate_file, store_file
from app.services.assessment_service import log_audit

router = APIRouter(prefix="/api/evidence", tags=["evidence"])


@router.post("/upload", response_model=EvidenceOut)
async def upload_evidence(
    assessment_id: uuid.UUID = Form(...),
    question_id: Optional[uuid.UUID] = Form(None),
    node_id: Optional[uuid.UUID] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any),
):
    content = await file.read()
    validate_file(file, len(content))
    meta = store_file(file, content)

    evidence = Evidence(
        assessment_id=assessment_id,
        question_id=question_id,
        node_id=node_id,
        file_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        file_size=meta["file_size"],
        storage_path=meta["storage_path"],
        checksum=meta["checksum"],
        uploaded_by=current_user.id,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    log_audit(db, current_user.id, "EVIDENCE_UPLOADED", "evidence", evidence.id, new_value=file.filename)
    return evidence


@router.get("/assessment/{assessment_id}", response_model=list[EvidenceOut])
def list_evidence_for_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    return db.query(Evidence).filter(Evidence.assessment_id == assessment_id).all()


@router.get("/{evidence_id}")
def download_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Evidence not found", "error_code": "EVIDENCE_NOT_FOUND"})
    return FileResponse(evidence.storage_path, filename=evidence.file_name)


@router.delete("/{evidence_id}")
def delete_evidence(evidence_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Evidence not found", "error_code": "EVIDENCE_NOT_FOUND"})
    db.delete(evidence)
    db.commit()
    log_audit(db, current_user.id, "EVIDENCE_DELETED", "evidence", evidence_id)
    return {"success": True, "message": "Evidence deleted"}
