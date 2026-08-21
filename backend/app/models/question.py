import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, Text, Enum, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class QuestionType(str, enum.Enum):
    YES_NO = "YES_NO"
    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_CHOICE = "MULTIPLE_CHOICE"
    TEXT = "TEXT"


class Question(Base):
    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    help_text = Column(Text)
    question_type = Column(Enum(QuestionType), nullable=False, default=QuestionType.YES_NO)
    weight = Column(Float, default=1.0)
    display_order = Column(Integer, default=0)
    is_mandatory = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan")
    mappings = relationship("QuestionMapping", back_populates="question", cascade="all, delete-orphan")


class QuestionOption(Base):
    """Answer options for a question, each with its own risk score/level."""
    __tablename__ = "question_options"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    label = Column(String, nullable=False)  # e.g. "Yes", "No", "Sometimes"
    value = Column(String, nullable=False)  # machine value stored in answers
    risk_score = Column(Float, default=0)
    risk_level = Column(String, default="LOW")
    display_order = Column(Integer, default=0)

    question = relationship("Question", back_populates="options")


class QuestionMapping(Base):
    """Maps a question to a LINDDUN category + specific threat node."""
    __tablename__ = "question_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linddun_categories.id"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("linddun_nodes.id"), nullable=True)

    question = relationship("Question", back_populates="mappings")
    category = relationship("LinddunCategory")
    node = relationship("LinddunNode")
