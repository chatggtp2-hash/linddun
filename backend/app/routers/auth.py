from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import verify_password, create_access_token
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse
from app.services.assessment_service import log_audit

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail={"success": False, "message": "Invalid email or password", "error_code": "INVALID_CREDENTIALS"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail={"success": False, "message": "User account is disabled", "error_code": "USER_INACTIVE"},
        )
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    log_audit(db, user.id, "LOGIN", "user", user.id, request.client.host if request.client else None)
    return TokenResponse(access_token=token, user=user)
