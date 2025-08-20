from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

class ChatSettings(BaseModel):
    model: str = "gpt-4"
    temperature: float = 0.7
    maxTokens: int = 2000
    webBrowsing: bool = False
    deepResearch: bool = False
    includeDocuments: List[str] = []

class ChatSessionCreate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: UUID
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    status: str
    session_metadata: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
    message_count: int
    total_tokens: int
    messages: Optional[List['ChatMessageResponse']] = None

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    content: str
    role: str = "user"
    settings: ChatSettings
    context_options: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    session_id: UUID
    role: str
    content: str
    timestamp: datetime
    tokens: Optional[int] = None
    model: Optional[str] = None
    message_metadata: Dict[str, Any] = {}
    document_references: List[Dict[str, Any]] = []
    annotation_references: List[str] = []

    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    description: str
    priority: str = "medium"

class TaskUpdate(BaseModel):
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    description: str
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime] = None

class ContextUpdate(BaseModel):
    summary: Optional[str] = None
    current_goal: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    relevant_documents: Optional[List[str]] = None

class ChatContextUpdate(BaseModel):
    summary: Optional[str] = None
    current_goal: Optional[str] = None
    tasks: Optional[List[Dict[str, Any]]] = None
    relevant_documents: Optional[List[str]] = None

class StreamingResponse(BaseModel):
    type: str  # "chunk", "complete", "error"
    content: str = ""
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ContextResponse(BaseModel):
    session_id: UUID
    summary: Optional[str] = None
    current_goal: Optional[str] = None
    tasks: List[Dict[str, Any]] = []
    relevant_documents: List[str] = []
    updated_at: datetime

    class Config:
        from_attributes = True

# Forward reference resolution
ChatSessionResponse.model_rebuild()