from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, String as SQLString
from datetime import datetime
import uuid

from app.core.database import Base

class UUID(TypeDecorator):
    impl = SQLString
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(SQLString(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            return uuid.UUID(value)

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Annotation target (position in document)
    target = Column(JSON, nullable=False)
    
    # Annotation body (content)
    body = Column(JSON, nullable=False)
    
    # Threading
    reply_to = Column(UUID(), ForeignKey("annotations.id"), nullable=True)
    thread_id = Column(UUID(), nullable=True)
    
    # Status
    resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="annotations")
    user = relationship("User", foreign_keys=[user_id], back_populates="annotations")
    resolver = relationship("User", foreign_keys=[resolved_by])
    replies = relationship("Annotation", backref="parent", remote_side=[id])
    
    # For PDF annotations
    page_number = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<Annotation(id='{self.id}', document_id='{self.document_id}')>"