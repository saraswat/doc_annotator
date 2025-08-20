from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), default="New Chat")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="active")  # active, archived
    
    # Metadata
    metadata = Column(JSON, default={})
    settings = Column(JSON, default={})
    
    # Statistics
    message_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    context = relationship("ChatContext", back_populates="session", uselist=False, cascade="all, delete-orphan")
    
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Token tracking
    tokens = Column(Integer)
    model = Column(String(50))
    
    # Metadata for references and context
    metadata = Column(JSON, default={})
    
    # Document references
    document_references = Column(JSON, default=[])
    annotation_references = Column(JSON, default=[])
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")

class ChatContext(Base):
    __tablename__ = "chat_contexts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), unique=True, nullable=False)
    
    # Problem solving context
    summary = Column(Text)
    current_goal = Column(String(500))
    tasks = Column(JSON, default=[])
    
    # Related documents
    relevant_documents = Column(JSON, default=[])
    
    # Context embeddings for similarity search
    embedding = Column(JSON)  # Store as JSON array
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ChatSession", back_populates="context")