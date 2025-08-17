from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base

class DocumentType(enum.Enum):
    HTML = "html"
    MARKDOWN = "markdown"  
    PDF = "pdf"
    TEXT = "text"

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    
    # Document type and content
    document_type = Column(Enum(DocumentType), nullable=False)
    content = Column(Text, nullable=True)  # For HTML/Markdown content
    content_hash = Column(String, nullable=True)  # For change detection
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array as string
    
    # Key-Date organization (e.g., person name and year for tax returns)
    document_key = Column(String, nullable=True, index=True)  # e.g., "John Smith" 
    document_date = Column(String, nullable=True, index=True)  # e.g., "2024"
    
    # Ownership and permissions
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    allow_comments = Column(Boolean, default=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    processing_status = Column(String, default="completed")  # processing, completed, failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="documents")
    annotations = relationship("Annotation", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(title='{self.title}', type='{self.document_type.value}')>"