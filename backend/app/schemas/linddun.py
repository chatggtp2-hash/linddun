import uuid
from typing import Optional, List

from pydantic import BaseModel


class LinddunCategoryOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    short_description: Optional[str]
    risk_definition: Optional[str]
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class LinddunNodeCreate(BaseModel):
    category_id: uuid.UUID
    parent_id: Optional[uuid.UUID] = None
    code: str
    name: str
    description: Optional[str] = None
    recommended_controls: Optional[str] = None
    display_order: int = 0


class LinddunNodeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    recommended_controls: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class LinddunNodeOut(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    parent_id: Optional[uuid.UUID]
    code: str
    name: str
    description: Optional[str]
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True


class TreeNode(BaseModel):
    """Shape returned by the tree engine - recursive, risk-annotated."""
    id: str
    code: str
    name: str
    risk: str
    score: float
    question_count: int = 0
    evidence_count: int = 0
    children: List["TreeNode"] = []


TreeNode.model_rebuild()
