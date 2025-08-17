from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

class AnnotationTarget(BaseModel):
    selector: Dict[str, Any]
    source: Optional[str] = None

class AnnotationBody(BaseModel):
    type: str  # 'TextualBody', 'Highlight', 'Tag'
    value: str
    purpose: str  # 'commenting', 'highlighting', 'tagging', 'questioning'
    color: Optional[str] = None
    tags: Optional[List[str]] = None

class AnnotationBase(BaseModel):
    target: AnnotationTarget
    body: AnnotationBody
    page_number: Optional[int] = None

class AnnotationCreate(AnnotationBase):
    document_id: int
    reply_to: Optional[UUID] = None

class AnnotationUpdate(BaseModel):
    body: Optional[AnnotationBody] = None
    resolved: Optional[bool] = None

class AnnotationInDBBase(AnnotationBase):
    id: UUID
    document_id: int
    user_id: int
    reply_to: Optional[UUID] = None
    thread_id: Optional[UUID] = None
    resolved: bool
    resolved_by: Optional[int] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Annotation(AnnotationInDBBase):
    pass

class AnnotationResponse(AnnotationInDBBase):
    user_name: str
    user_avatar: Optional[str] = None
    can_edit: bool = False
    can_delete: bool = False

class AnnotationWithReplies(AnnotationResponse):
    replies: List[AnnotationResponse] = []