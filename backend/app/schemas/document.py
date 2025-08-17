from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.document import DocumentType

class DocumentBase(BaseModel):
    title: str
    description: Optional[str] = None
    tags: Optional[str] = None
    document_key: Optional[str] = None
    document_date: Optional[str] = None
    is_public: bool = False
    allow_comments: bool = True

class DocumentCreate(DocumentBase):
    document_type: DocumentType
    content: Optional[str] = None

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    document_key: Optional[str] = None
    document_date: Optional[str] = None
    is_public: Optional[bool] = None
    allow_comments: Optional[bool] = None

class DocumentInDBBase(DocumentBase):
    id: int
    filename: str
    file_path: str
    file_size: int
    document_type: DocumentType
    content: Optional[str] = None
    content_hash: Optional[str] = None
    owner_id: int
    is_active: bool
    processing_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class Document(DocumentInDBBase):
    pass

class DocumentResponse(DocumentInDBBase):
    pass

class DocumentListResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    document_type: DocumentType
    document_key: Optional[str] = None
    document_date: Optional[str] = None
    file_size: int
    owner_id: int
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True