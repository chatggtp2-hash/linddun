import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EvidenceOut(BaseModel):
    id: uuid.UUID
    assessment_id: uuid.UUID
    question_id: Optional[uuid.UUID]
    node_id: Optional[uuid.UUID]
    file_name: str
    file_type: str
    file_size: int
    uploaded_by: uuid.UUID
    uploaded_at: datetime

    class Config:
        from_attributes = True
