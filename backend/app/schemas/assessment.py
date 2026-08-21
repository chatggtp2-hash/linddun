import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.assessment import AssessmentStatus


class AssessmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    question_ids: List[uuid.UUID] = []  # questionnaire to attach; empty = all active questions


class AssessmentOut(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    status: AssessmentStatus
    owner_id: uuid.UUID
    overall_score: Optional[float]
    overall_risk_level: Optional[str]
    created_at: datetime
    submitted_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    question_id: uuid.UUID
    selected_option_id: Optional[uuid.UUID] = None
    text_response: Optional[str] = None


class AnswerOut(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    selected_option_id: Optional[uuid.UUID]
    text_response: Optional[str]
    computed_score: float

    class Config:
        from_attributes = True


class CategoryResultOut(BaseModel):
    category_id: uuid.UUID
    category_name: str
    score: float
    risk_level: str


class AssessmentResultOut(BaseModel):
    assessment: AssessmentOut
    category_results: List[CategoryResultOut]
    top_threats: List[dict]
    recommendations: List[str]
