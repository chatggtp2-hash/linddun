import uuid
from typing import Optional, List

from pydantic import BaseModel

from app.models.question import QuestionType


class QuestionOptionIn(BaseModel):
    label: str
    value: str
    risk_score: float
    risk_level: str
    display_order: int = 0


class QuestionOptionOut(QuestionOptionIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class QuestionMappingIn(BaseModel):
    category_id: uuid.UUID
    node_id: Optional[uuid.UUID] = None


class QuestionMappingOut(QuestionMappingIn):
    id: uuid.UUID

    class Config:
        from_attributes = True


class QuestionCreate(BaseModel):
    text: str
    help_text: Optional[str] = None
    question_type: QuestionType = QuestionType.YES_NO
    weight: float = 1.0
    display_order: int = 0
    is_mandatory: bool = True
    is_active: bool = True
    options: List[QuestionOptionIn] = []
    mappings: List[QuestionMappingIn] = []


class QuestionUpdate(BaseModel):
    text: Optional[str] = None
    help_text: Optional[str] = None
    question_type: Optional[QuestionType] = None
    weight: Optional[float] = None
    display_order: Optional[int] = None
    is_mandatory: Optional[bool] = None
    is_active: Optional[bool] = None
    options: Optional[List[QuestionOptionIn]] = None
    mappings: Optional[List[QuestionMappingIn]] = None


class QuestionOut(BaseModel):
    id: uuid.UUID
    text: str
    help_text: Optional[str]
    question_type: QuestionType
    weight: float
    display_order: int
    is_mandatory: bool
    is_active: bool
    options: List[QuestionOptionOut] = []
    mappings: List[QuestionMappingOut] = []

    class Config:
        from_attributes = True
