import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Enum, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class AssessmentStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    REVIEWER_REVIEW = "REVIEWER_REVIEW"
    RISK_CALCULATED = "RISK_CALCULATED"
    APPROVED = "APPROVED"
    REWORK = "REWORK"
    COMPLETED = "COMPLETED"


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(AssessmentStatus), nullable=False, default=AssessmentStatus.DRAFT)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    framework_version_id = Column(UUID(as_uuid=True), ForeignKey("framework_versions.id"), nullable=False)
    overall_score = Column(Float, nullable=True)
    overall_risk_level = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    answers = relationship("Answer", back_populates="assessment", cascade="all, delete-orphan")
    results = relationship("AssessmentResult", back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(Base):
    """Which questions are assigned to a given assessment (its questionnaire)."""
    __tablename__ = "assessment_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    display_order = Column(Integer, default=0)


class Answer(Base):
    __tablename__ = "answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    selected_option_id = Column(UUID(as_uuid=True), ForeignKey("question_options.id"), nullable=True)
    text_response = Column(Text, nullable=True)
    computed_score = Column(Float, default=0)
    answered_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    answered_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="answers")
    question = relationship("Question")
    selected_option = relationship("QuestionOption")


class AssessmentResult(Base):
    """Snapshot of computed risk per LINDDUN category/node for an assessment."""
    __tablename__ = "assessment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linddun_categories.id"), nullable=True)
    node_id = Column(UUID(as_uuid=True), ForeignKey("linddun_nodes.id"), nullable=True)
    score = Column(Float, default=0)
    risk_level = Column(String, default="LOW")
    calculated_at = Column(DateTime, default=datetime.utcnow)

    assessment = relationship("Assessment", back_populates="results")
