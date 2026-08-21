import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.middleware.permissions import require_admin, require_any
from app.models.question import Question, QuestionOption, QuestionMapping
from app.models.user import User
from app.schemas.question import QuestionCreate, QuestionUpdate, QuestionOut
from app.services.assessment_service import log_audit

router = APIRouter(prefix="/api/questions", tags=["questions"])


def _q_query(db: Session):
    return db.query(Question).options(
        joinedload(Question.options), joinedload(Question.mappings)
    )


@router.get("", response_model=list[QuestionOut])
def list_questions(active_only: bool = False, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    q = _q_query(db)
    if active_only:
        q = q.filter(Question.is_active == True)  # noqa: E712
    return q.order_by(Question.display_order).all()


@router.post("", response_model=QuestionOut)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    question = Question(
        text=payload.text,
        help_text=payload.help_text,
        question_type=payload.question_type,
        weight=payload.weight,
        display_order=payload.display_order,
        is_mandatory=payload.is_mandatory,
        is_active=payload.is_active,
        created_by=current_user.id,
    )
    db.add(question)
    db.flush()

    for opt in payload.options:
        db.add(QuestionOption(question_id=question.id, **opt.dict()))
    for m in payload.mappings:
        db.add(QuestionMapping(question_id=question.id, **m.dict()))

    db.commit()
    db.refresh(question)
    log_audit(db, current_user.id, "QUESTION_CREATED", "question", question.id, new_value=payload.text)
    return _q_query(db).filter(Question.id == question.id).first()


@router.get("/{question_id}", response_model=QuestionOut)
def get_question(question_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    question = _q_query(db).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Question not found", "error_code": "QUESTION_NOT_FOUND"})
    return question


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(question_id: uuid.UUID, payload: QuestionUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Question not found", "error_code": "QUESTION_NOT_FOUND"})

    old_text = question.text
    data = payload.dict(exclude_unset=True, exclude={"options", "mappings"})
    for k, v in data.items():
        setattr(question, k, v)

    if payload.options is not None:
        db.query(QuestionOption).filter(QuestionOption.question_id == question.id).delete()
        for opt in payload.options:
            db.add(QuestionOption(question_id=question.id, **opt.dict()))

    if payload.mappings is not None:
        db.query(QuestionMapping).filter(QuestionMapping.question_id == question.id).delete()
        for m in payload.mappings:
            db.add(QuestionMapping(question_id=question.id, **m.dict()))

    db.commit()
    log_audit(db, current_user.id, "QUESTION_UPDATED", "question", question.id, previous_value=old_text, new_value=question.text)
    return _q_query(db).filter(Question.id == question.id).first()


@router.delete("/{question_id}")
def delete_question(question_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Question not found", "error_code": "QUESTION_NOT_FOUND"})
    question.is_active = False  # soft delete / deactivate
    db.commit()
    log_audit(db, current_user.id, "QUESTION_DELETED", "question", question.id)
    return {"success": True, "message": "Question deactivated"}
