import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Boolean, DateTime, Integer, ForeignKey, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class FrameworkVersion(Base):
    """Allows the LINDDUN tree to evolve without breaking historical results."""
    __tablename__ = "framework_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_label = Column(String, nullable=False, unique=True)  # e.g. "v1"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    categories = relationship("LinddunCategory", back_populates="framework_version")


class LinddunCategory(Base):
    """The 7 top-level LINDDUN categories (Linkability, Identifiability, ...)."""
    __tablename__ = "linddun_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False)  # e.g. "L", "I", "NR"
    name = Column(String, nullable=False)
    description = Column(Text)
    short_description = Column(String)
    risk_definition = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    framework_version_id = Column(UUID(as_uuid=True), ForeignKey("framework_versions.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    framework_version = relationship("FrameworkVersion", back_populates="categories")
    nodes = relationship("LinddunNode", back_populates="category", cascade="all, delete-orphan")


class LinddunNode(Base):
    """A node in a category's threat tree. Self-referential parent/child."""
    __tablename__ = "linddun_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linddun_categories.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("linddun_nodes.id"), nullable=True)
    code = Column(String, nullable=False)  # e.g. "NR-1-2"
    name = Column(String, nullable=False)
    description = Column(Text)
    recommended_controls = Column(Text)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("LinddunCategory", back_populates="nodes")
    parent = relationship("LinddunNode", remote_side=[id], backref="children")


class RecommendationRule(Base):
    """Rule-based recommendation engine: category/node + risk level -> action text."""
    __tablename__ = "recommendation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_id = Column(UUID(as_uuid=True), ForeignKey("linddun_categories.id"), nullable=True)
    node_id = Column(UUID(as_uuid=True), ForeignKey("linddun_nodes.id"), nullable=True)
    trigger_risk_level = Column(String, nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL
    recommendation_text = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)


class RiskThreshold(Base):
    """Configurable risk-band thresholds instead of hard-coded values."""
    __tablename__ = "risk_thresholds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level_name = Column(String, nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL
    min_score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    display_order = Column(Integer, default=0)
