import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.permissions import require_any
from app.models.assessment import Assessment, AssessmentQuestion, Answer, AssessmentStatus, AssessmentResult
from app.models.question import Question, QuestionMapping
from app.models.linddun import FrameworkVersion, LinddunCategory
from app.models.user import User, RoleEnum
from app.schemas.assessment import AssessmentCreate, AssessmentOut, AnswerSubmit, AnswerOut, CategoryResultOut, AssessmentResultOut
from app.services.risk_engine import calculate_assessment_risk
from app.services.tree_engine import build_full_tree
from app.services.recommendation_engine import get_recommendations
from app.services.assessment_service import log_audit

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


def _get_owned_assessment(db: Session, assessment_id: uuid.UUID, current_user: User) -> Assessment:
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail={"success": False, "message": "Assessment not found", "error_code": "ASSESSMENT_NOT_FOUND"})
    if current_user.role == RoleEnum.ASSESSOR and assessment.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail={"success": False, "message": "You cannot access another user's assessment", "error_code": "FORBIDDEN"})
    return assessment


@router.post("", response_model=AssessmentOut)
def create_assessment(payload: AssessmentCreate, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    framework = db.query(FrameworkVersion).filter(FrameworkVersion.is_active == True).first()  # noqa: E712
    if not framework:
        raise HTTPException(status_code=500, detail={"success": False, "message": "No active framework version", "error_code": "NO_FRAMEWORK"})

    assessment = Assessment(
        name=payload.name,
        description=payload.description,
        status=AssessmentStatus.DRAFT,
        owner_id=current_user.id,
        framework_version_id=framework.id,
    )
    db.add(assessment)
    db.flush()

    question_ids = payload.question_ids
    if not question_ids:
        question_ids = [q.id for q in db.query(Question).filter(Question.is_active == True).all()]  # noqa: E712

    for i, qid in enumerate(question_ids):
        db.add(AssessmentQuestion(assessment_id=assessment.id, question_id=qid, display_order=i))

    db.commit()
    db.refresh(assessment)
    log_audit(db, current_user.id, "ASSESSMENT_CREATED", "assessment", assessment.id, new_value=assessment.name)
    return assessment


@router.get("", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    q = db.query(Assessment)
    if current_user.role == RoleEnum.ASSESSOR:
        q = q.filter(Assessment.owner_id == current_user.id)
    return q.order_by(Assessment.created_at.desc()).all()


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    return _get_owned_assessment(db, assessment_id, current_user)


@router.get("/{assessment_id}/questions")
def get_assessment_questions(assessment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessment = _get_owned_assessment(db, assessment_id, current_user)
    aqs = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id == assessment.id)
        .order_by(AssessmentQuestion.display_order)
        .all()
    )
    existing_answers = {a.question_id: a for a in db.query(Answer).filter(Answer.assessment_id == assessment.id).all()}

    out = []
    for aq in aqs:
        question = db.query(Question).filter(Question.id == aq.question_id).first()
        if not question:
            continue
        mapping = db.query(QuestionMapping).filter(QuestionMapping.question_id == question.id).first()
        category = db.query(LinddunCategory).filter(LinddunCategory.id == mapping.category_id).first() if mapping else None
        answer = existing_answers.get(question.id)
        out.append({
            "question_id": str(question.id),
            "text": question.text,
            "help_text": question.help_text,
            "question_type": question.question_type,
            "is_mandatory": question.is_mandatory,
            "options": [
                {"id": str(o.id), "label": o.label, "value": o.value} for o in question.options
            ],
            "mapped_category": category.name if category else None,
            "mapped_risk_hint": mapping.node_id and str(mapping.node_id) or None,
            "existing_answer": {
                "selected_option_id": str(answer.selected_option_id) if answer and answer.selected_option_id else None,
                "text_response": answer.text_response if answer else None,
            } if answer else None,
        })
    return out


@router.post("/{assessment_id}/answers", response_model=AnswerOut)
def submit_answer(assessment_id: uuid.UUID, payload: AnswerSubmit, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessment = _get_owned_assessment(db, assessment_id, current_user)
    if assessment.status not in (AssessmentStatus.DRAFT, AssessmentStatus.IN_PROGRESS, AssessmentStatus.REWORK):
        raise HTTPException(status_code=409, detail={"success": False, "message": "Assessment is not editable in its current status", "error_code": "ASSESSMENT_LOCKED"})

    existing = (
        db.query(Answer)
        .filter(Answer.assessment_id == assessment.id, Answer.question_id == payload.question_id)
        .first()
    )
    if existing:
        existing.selected_option_id = payload.selected_option_id
        existing.text_response = payload.text_response
        existing.answered_by = current_user.id
        answer = existing
    else:
        answer = Answer(
            assessment_id=assessment.id,
            question_id=payload.question_id,
            selected_option_id=payload.selected_option_id,
            text_response=payload.text_response,
            answered_by=current_user.id,
        )
        db.add(answer)

    if assessment.status == AssessmentStatus.DRAFT:
        assessment.status = AssessmentStatus.IN_PROGRESS

    db.commit()
    db.refresh(answer)
    log_audit(db, current_user.id, "ANSWER_SUBMITTED", "answer", answer.id, new_value=str(payload.selected_option_id))
    return answer


@router.post("/{assessment_id}/submit", response_model=AssessmentResultOut)
def submit_assessment(assessment_id: uuid.UUID, request: Request, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessment = _get_owned_assessment(db, assessment_id, current_user)
    if assessment.status not in (AssessmentStatus.IN_PROGRESS, AssessmentStatus.DRAFT, AssessmentStatus.REWORK):
        raise HTTPException(status_code=409, detail={"success": False, "message": "Assessment already submitted", "error_code": "ALREADY_SUBMITTED"})

    # mandatory question check
    aqs = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == assessment.id).all()
    answered_ids = {a.question_id for a in db.query(Answer).filter(Answer.assessment_id == assessment.id).all()}
    missing = []
    for aq in aqs:
        question = db.query(Question).filter(Question.id == aq.question_id).first()
        if question and question.is_mandatory and question.id not in answered_ids:
            missing.append(question.text)
    if missing:
        raise HTTPException(status_code=422, detail={"success": False, "message": "Mandatory questions unanswered", "error_code": "VALIDATION_ERROR", "missing": missing})

    assessment.status = AssessmentStatus.SUBMITTED
    assessment.submitted_at = datetime.utcnow()
    db.commit()
    log_audit(db, current_user.id, "ASSESSMENT_SUBMITTED", "assessment", assessment.id, ip_address=request.client.host if request.client else None)

    # risk engine runs automatically on submit
    calculate_assessment_risk(db, assessment)
    assessment.status = AssessmentStatus.RISK_CALCULATED
    assessment.completed_at = datetime.utcnow()
    assessment.status = AssessmentStatus.COMPLETED
    db.commit()
    log_audit(db, current_user.id, "RISK_CALCULATED", "assessment", assessment.id, new_value=str(assessment.overall_score))

    return _build_result(db, assessment)


@router.get("/{assessment_id}/result", response_model=AssessmentResultOut)
def get_result(assessment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessment = _get_owned_assessment(db, assessment_id, current_user)
    return _build_result(db, assessment)


@router.get("/{assessment_id}/tree")
def get_assessment_tree(assessment_id: uuid.UUID, db: Session = Depends(get_db), current_user: User = Depends(require_any)):
    assessment = _get_owned_assessment(db, assessment_id, current_user)
    return build_full_tree(db, str(assessment.id))


def _build_result(db: Session, assessment: Assessment) -> dict:
    cat_results = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.assessment_id == assessment.id, AssessmentResult.category_id.isnot(None))
        .all()
    )
    category_out = []
    for r in cat_results:
        category = db.query(LinddunCategory).filter(LinddunCategory.id == r.category_id).first()
        category_out.append(CategoryResultOut(
            category_id=r.category_id, category_name=category.name if category else "Unknown",
            score=r.score, risk_level=r.risk_level,
        ))
    category_out.sort(key=lambda c: c.score, reverse=True)

    top_threats = [
        {"name": c.category_name, "risk_level": c.risk_level, "score": c.score}
        for c in category_out[:5]
    ]

    recommendations = get_recommendations(db, str(assessment.id))

    return {
        "assessment": assessment,
        "category_results": category_out,
        "top_threats": top_threats,
        "recommendations": recommendations,
    }
