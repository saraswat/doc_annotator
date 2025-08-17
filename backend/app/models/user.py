from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    
    # OAuth fields
    oauth_provider = Column(String, nullable=False)  # google, azure, okta
    oauth_id = Column(String, nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("Document", back_populates="owner")
    annotations = relationship("Annotation", back_populates="user", foreign_keys="Annotation.user_id")
    
    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}')>"