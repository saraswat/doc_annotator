# React + FastAPI Document Annotation System
## Complete Implementation Guide for Claude for Code

## Project Overview
Build a professional document annotation system similar to Google Docs or Adobe Acrobat comments. Users can select text within documents and add inline annotations (comments, highlights, tags). The system supports HTML, Markdown, and PDF documents with OAuth authentication and real-time collaboration capabilities.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   OAuth     │  │   Document   │  │  Annotation  │  │
│  │   Login     │  │    Viewer    │  │    Tools     │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │ REST API + WebSocket
┌─────────────────────────┴───────────────────────────────┐
│                   FastAPI Backend                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Auth     │  │   Document   │  │  Annotation  │  │
│  │   Handler   │  │   Storage    │  │    Service   │  │
│  └─────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────┬───────────────────────────────┘
                          │
                    ┌─────┴─────┐
                    │PostgreSQL │
                    └───────────┘
```

## Complete Project Structure

```
document-annotation-system/
├── frontend/                      # React TypeScript application
│   ├── package.json
│   ├── tsconfig.json
│   ├── .env.example
│   ├── public/
│   │   └── index.html
│   └── src/
│       ├── index.tsx
│       ├── App.tsx
│       ├── types/
│       │   ├── annotation.ts     # TypeScript interfaces
│       │   ├── document.ts
│       │   └── user.ts
│       ├── components/
│       │   ├── Layout/
│       │   │   ├── Header.tsx
│       │   │   ├── Sidebar.tsx
│       │   │   └── Layout.tsx
│       │   ├── Auth/
│       │   │   ├── LoginPage.tsx
│       │   │   ├── OAuthCallback.tsx
│       │   │   └── ProtectedRoute.tsx
│       │   ├── DocumentViewer/
│       │   │   ├── DocumentViewer.tsx
│       │   │   ├── HtmlViewer.tsx
│       │   │   ├── PdfViewer.tsx
│       │   │   └── AnnotationLayer.tsx
│       │   ├── AnnotationTools/
│       │   │   ├── TextSelector.tsx
│       │   │   ├── AnnotationPopup.tsx
│       │   │   ├── CommentThread.tsx
│       │   │   └── HighlightMenu.tsx
│       │   └── Sidebar/
│       │       ├── DocumentList.tsx
│       │       ├── AnnotationList.tsx
│       │       └── UserInfo.tsx
│       ├── contexts/
│       │   ├── AuthContext.tsx
│       │   ├── DocumentContext.tsx
│       │   └── AnnotationContext.tsx
│       ├── hooks/
│       │   ├── useAnnotations.ts
│       │   ├── useWebSocket.ts
│       │   └── useTextSelection.ts
│       ├── services/
│       │   ├── api.ts
│       │   ├── auth.ts
│       │   ├── documents.ts
│       │   └── annotations.ts
│       ├── utils/
│       │   ├── textSelection.ts
│       │   ├── annotationHelpers.ts
│       │   └── pdfHelpers.ts
│       └── styles/
│           ├── globals.css
│           └── annotations.css
│
├── backend/                       # FastAPI Python application
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic.ini               # Database migrations
│   ├── main.py                   # FastAPI entry point
│   ├── app/
│   │   ├── __init__.py
│   │   ├── core/
│   │   │   ├── config.py        # Settings and configuration
│   │   │   ├── security.py      # OAuth and JWT handling
│   │   │   └── database.py      # Database connection
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── annotation.py
│   │   ├── schemas/              # Pydantic models
│   │   │   ├── user.py
│   │   │   ├── document.py
│   │   │   └── annotation.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # OAuth endpoints
│   │   │   ├── documents.py     # Document CRUD
│   │   │   ├── annotations.py   # Annotation CRUD
│   │   │   └── websocket.py     # Real-time updates
│   │   ├── services/
│   │   │   ├── document_processor.py
│   │   │   ├── annotation_service.py
│   │   │   └── pdf_service.py
│   │   └── utils/
│   │       ├── document_converter.py
│   │       └── text_extraction.py
│   ├── migrations/               # Alembic migrations
│   └── tests/
│
├── docker-compose.yml            # Development environment
└── README.md
```

## Frontend Implementation (React + TypeScript)

### 1. Package.json
```json
{
  "name": "document-annotation-frontend",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0",
    
    "@recogito/recogito-js": "^1.8.0",
    "react-pdf": "^7.7.0",
    "pdfjs-dist": "^3.11.0",
    
    "@mui/material": "^5.15.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.15.0",
    
    "rangy": "^1.3.0",
    "uuid": "^9.0.0",
    "date-fns": "^3.0.0",
    "react-markdown": "^9.0.0",
    "remark-gfm": "^4.0.0",
    "react-hot-toast": "^2.4.0",
    "zustand": "^4.4.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  },
  "devDependencies": {
    "@types/uuid": "^9.0.0",
    "@types/rangy": "^0.0.35",
    "react-scripts": "5.0.1"
  }
}
```

### 2. TypeScript Types (src/types/annotation.ts)
```typescript
export interface Annotation {
  id: string;
  documentId: string;
  userId: string;
  userName: string;
  userAvatar?: string;
  createdAt: Date;
  updatedAt?: Date;
  
  // Position in document
  target: AnnotationTarget;
  
  // Annotation content
  body: AnnotationBody;
  
  // Threading and status
  replies?: Annotation[];
  replyTo?: string;
  resolved: boolean;
  resolvedBy?: string;
  resolvedAt?: Date;
  
  // For PDF documents
  pageNumber?: number;
  
  // Permissions
  canEdit: boolean;
  canDelete: boolean;
}

export interface AnnotationTarget {
  selector: TextSelector | XPathSelector;
  source?: string;  // Document URL or ID
}

export interface TextSelector {
  type: 'TextQuoteSelector' | 'TextPositionSelector';
  exact: string;      // The exact quoted text
  prefix?: string;    // Text before the quote
  suffix?: string;    // Text after the quote
  start?: number;     // Start position
  end?: number;       // End position
}

export interface XPathSelector {
  type: 'XPathSelector';
  xpath: string;
  offset?: number;
}

export interface AnnotationBody {
  type: 'TextualBody' | 'Highlight' | 'Tag';
  value: string;
  purpose: 'commenting' | 'highlighting' | 'tagging' | 'questioning';
  color?: string;  // For highlights
  tags?: string[]; // For categorization
}

export interface CreateAnnotationDto {
  documentId: string;
  target: AnnotationTarget;
  body: AnnotationBody;
  replyTo?: string;
}
```

### 3. Main Document Viewer Component (src/components/DocumentViewer/DocumentViewer.tsx)
```typescript
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Box, Paper, CircularProgress } from '@mui/material';
import Recogito from '@recogito/recogito-js';
import '@recogito/recogito-js/dist/recogito.min.css';
import { Annotation, CreateAnnotationDto } from '../../types/annotation';
import { Document } from '../../types/document';
import { useAnnotations } from '../../hooks/useAnnotations';
import { useWebSocket } from '../../hooks/useWebSocket';
import AnnotationPopup from '../AnnotationTools/AnnotationPopup';
import { annotationService } from '../../services/annotations';

interface DocumentViewerProps {
  document: Document;
  currentUser: User;
}

const DocumentViewer: React.FC<DocumentViewerProps> = ({ document, currentUser }) => {
  const contentRef = useRef<HTMLDivElement>(null);
  const recogitoRef = useRef<any>(null);
  const [selectedAnnotation, setSelectedAnnotation] = useState<Annotation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const { annotations, addAnnotation, updateAnnotation, deleteAnnotation } = useAnnotations(document.id);
  const { subscribe, unsubscribe } = useWebSocket();

  // Initialize Recogito annotation library
  useEffect(() => {
    if (!contentRef.current || !document.content) return;

    // Initialize Recogito
    recogitoRef.current = new Recogito({
      content: contentRef.current,
      locale: 'en',
      allowEmpty: false,
      mode: 'pre', // 'pre' for pre-selection popup, 'click' for click to annotate
      widgets: [
        { widget: 'COMMENT' },
        { widget: 'TAG', vocabulary: ['Important', 'Question', 'Feedback', 'Error'] },
        { 
          widget: 'COLOR',
          colors: {
            'yellow': '#FFE900',
            'green': '#00CED1',
            'pink': '#FF6B6B',
            'purple': '#9B59B6'
          }
        }
      ],
      formatter: (annotation: any) => {
        // Custom formatting for different annotation types
        const className = [];
        if (annotation.body?.purpose === 'highlighting') {
          className.push(`highlight-${annotation.body.color || 'yellow'}`);
        }
        if (annotation.resolved) {
          className.push('annotation-resolved');
        }
        return className.join(' ');
      }
    });

    // Load existing annotations
    const recogitoAnnotations = convertToRecogitoFormat(annotations);
    recogitoRef.current.setAnnotations(recogitoAnnotations);

    // Handle annotation creation
    recogitoRef.current.on('createAnnotation', async (annotation: any) => {
      const dto = convertFromRecogitoFormat(annotation, document.id, currentUser);
      const created = await annotationService.create(dto);
      addAnnotation(created);
    });

    // Handle annotation updates
    recogitoRef.current.on('updateAnnotation', async (annotation: any, previous: any) => {
      const updated = await annotationService.update(annotation.id, annotation);
      updateAnnotation(updated);
    });

    // Handle annotation deletion
    recogitoRef.current.on('deleteAnnotation', async (annotation: any) => {
      await annotationService.delete(annotation.id);
      deleteAnnotation(annotation.id);
    });

    // Handle annotation selection
    recogitoRef.current.on('selectAnnotation', (annotation: any) => {
      setSelectedAnnotation(annotation);
    });

    setIsLoading(false);

    return () => {
      if (recogitoRef.current) {
        recogitoRef.current.destroy();
      }
    };
  }, [document, annotations]);

  // Subscribe to WebSocket updates
  useEffect(() => {
    const handleAnnotationUpdate = (data: any) => {
      if (data.documentId === document.id) {
        switch (data.type) {
          case 'annotation_created':
            if (data.userId !== currentUser.id) {
              addAnnotation(data.annotation);
              recogitoRef.current?.addAnnotation(convertToRecogitoFormat([data.annotation])[0]);
            }
            break;
          case 'annotation_updated':
            updateAnnotation(data.annotation);
            break;
          case 'annotation_deleted':
            deleteAnnotation(data.annotationId);
            recogitoRef.current?.removeAnnotation(data.annotationId);
            break;
        }
      }
    };

    subscribe('annotation_update', handleAnnotationUpdate);

    return () => {
      unsubscribe('annotation_update', handleAnnotationUpdate);
    };
  }, [document.id, currentUser.id]);

  const renderDocumentContent = () => {
    switch (document.type) {
      case 'html':
        return (
          <div
            ref={contentRef}
            className="document-content"
            dangerouslySetInnerHTML={{ __html: document.content }}
          />
        );
      case 'markdown':
        return (
          <div ref={contentRef} className="document-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {document.content}
            </ReactMarkdown>
          </div>
        );
      case 'pdf':
        return <PdfViewer document={document} onAnnotation={handlePdfAnnotation} />;
      default:
        return <div>Unsupported document type</div>;
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper elevation={3} sx={{ height: '100%', overflow: 'auto', p: 4 }}>
      {renderDocumentContent()}
      
      {selectedAnnotation && (
        <AnnotationPopup
          annotation={selectedAnnotation}
          onClose={() => setSelectedAnnotation(null)}
          onReply={(text) => handleReply(selectedAnnotation.id, text)}
          onResolve={() => handleResolve(selectedAnnotation.id)}
          currentUser={currentUser}
        />
      )}
    </Paper>
  );
};

export default DocumentViewer;
```

### 4. WebSocket Hook (src/hooks/useWebSocket.ts)
```typescript
import { useEffect, useRef } from 'react';
import io, { Socket } from 'socket.io-client';
import { useAuthStore } from '../stores/authStore';

export const useWebSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const { token } = useAuthStore();

  useEffect(() => {
    if (!token) return;

    socketRef.current = io(process.env.REACT_APP_WS_URL || 'ws://localhost:8000', {
      auth: { token },
      transports: ['websocket'],
    });

    socketRef.current.on('connect', () => {
      console.log('WebSocket connected');
    });

    socketRef.current.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, [token]);

  const subscribe = (event: string, handler: (data: any) => void) => {
    socketRef.current?.on(event, handler);
  };

  const unsubscribe = (event: string, handler: (data: any) => void) => {
    socketRef.current?.off(event, handler);
  };

  const emit = (event: string, data: any) => {
    socketRef.current?.emit(event, data);
  };

  return { subscribe, unsubscribe, emit };
};
```

### 5. API Service (src/services/api.ts)
```typescript
import axios, { AxiosInstance } from 'axios';
import { toast } from 'react-hot-toast';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          await this.refreshToken();
        }
        return Promise.reject(error);
      }
    );
  }

  private async refreshToken() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      const response = await this.api.post('/auth/refresh', { 
        refresh_token: refreshToken 
      });
      localStorage.setItem('access_token', response.data.access_token);
      return response.data.access_token;
    } catch (error) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
      throw error;
    }
  }

  get(url: string, params?: any) {
    return this.api.get(url, { params });
  }

  post(url: string, data?: any) {
    return this.api.post(url, data);
  }

  put(url: string, data?: any) {
    return this.api.put(url, data);
  }

  patch(url: string, data?: any) {
    return this.api.patch(url, data);
  }

  delete(url: string) {
    return this.api.delete(url);
  }
}

export default new ApiService();
```

## Backend Implementation (FastAPI + Python)

### 1. Requirements.txt
```
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
authlib==1.3.0
httpx==0.26.0

sqlalchemy==2.0.25
alembic==1.13.1
asyncpg==0.29.0
psycopg2-binary==2.9.9

pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

beautifulsoup4==4.12.0
markdown==3.5.0
PyPDF2==3.0.0
pdfplumber==0.10.0
Pillow==10.2.0

redis==5.0.0
celery==5.3.0

python-socketio==5.11.0
websockets==12.0

boto3==1.34.0  # For S3 storage
minio==7.2.0   # Alternative to S3

pytest==7.4.0
pytest-asyncio==0.23.0
```

### 2. FastAPI Main Application (backend/main.py)
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import socketio

from app.core.config import settings
from app.core.database import create_db_and_tables
from app.api import auth, documents, annotations, websocket
from app.core.websocket import sio_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await create_db_and_tables()
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title="Document Annotation API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Socket.IO app
app.mount("/socket.io", sio_app)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(annotations.router, prefix="/api/annotations", tags=["annotations"])

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

### 3. Database Models (backend/app/models/annotation.py)
```python
from sqlalchemy import Column, String, Integer, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Annotation target (position in document)
    target = Column(JSON, nullable=False)
    
    # Annotation body (content)
    body = Column(JSON, nullable=False)
    
    # Threading
    reply_to = Column(UUID(as_uuid=True), ForeignKey("annotations.id"), nullable=True)
    thread_id = Column(UUID(as_uuid=True), nullable=True)
    
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
    
    class Config:
        orm_mode = True
```

### 4. Annotation API Endpoints (backend/app/api/annotations.py)
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models import Annotation, User
from app.schemas.annotation import (
    AnnotationCreate, 
    AnnotationUpdate, 
    AnnotationResponse,
    AnnotationWithReplies
)
from app.services.annotation_service import AnnotationService
from app.core.websocket import manager

router = APIRouter()

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new annotation."""
    service = AnnotationService(db)
    annotation = await service.create_annotation(
        annotation_data, 
        current_user.id
    )
    
    # Broadcast to WebSocket clients
    await manager.broadcast_to_document(
        annotation.document_id,
        {
            "type": "annotation_created",
            "annotation": annotation.dict(),
            "userId": current_user.id
        }
    )
    
    return annotation

@router.get("/document/{document_id}", response_model=List[AnnotationWithReplies])
async def get_document_annotations(
    document_id: int,
    include_resolved: bool = Query(True),
    page_number: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all annotations for a document."""
    service = AnnotationService(db)
    annotations = await service.get_document_annotations(
        document_id,
        include_resolved=include_resolved,
        page_number=page_number
    )
    return annotations

@router.patch("/{annotation_id}", response_model=AnnotationResponse)
async def update_annotation(
    annotation_id: UUID,
    update_data: AnnotationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Update an annotation."""
    service = AnnotationService(db)
    
    # Check permissions
    annotation = await service.get_annotation(annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    if annotation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this annotation")
    
    updated = await service.update_annotation(annotation_id, update_data)
    
    # Broadcast update
    await manager.broadcast_to_document(
        updated.document_id,
        {
            "type": "annotation_updated",
            "annotation": updated.dict(),
            "userId": current_user.id
        }
    )
    
    return updated

@router.delete("/{annotation_id}")
async def delete_annotation(
    annotation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete an annotation."""
    service = AnnotationService(db)
    
    # Check permissions
    annotation = await service.get_annotation(annotation_id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    if annotation.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete this annotation")
    
    await service.delete_annotation(annotation_id)
    
    # Broadcast deletion
    await manager.broadcast_to_document(
        annotation.document_id,
        {
            "type": "annotation_deleted",
            "annotationId": str(annotation_id),
            "userId": current_user.id
        }
    )
    
    return {"status": "deleted"}

@router.post("/{annotation_id}/resolve")
async def resolve_annotation(
    annotation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Mark an annotation as resolved."""
    service = AnnotationService(db)
    resolved = await service.resolve_annotation(annotation_id, current_user.id)
    
    # Broadcast resolution
    await manager.broadcast_to_document(
        resolved.document_id,
        {
            "type": "annotation_resolved",
            "annotationId": str(annotation_id),
            "resolvedBy": current_user.id
        }
    )
    
    return resolved

@router.post("/{annotation_id}/reply", response_model=AnnotationResponse)
async def reply_to_annotation(
    annotation_id: UUID,
    reply_data: AnnotationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Reply to an annotation (threading)."""
    service = AnnotationService(db)
    
    # Set the reply_to field
    reply_data.reply_to = annotation_id
    
    reply = await service.create_annotation(reply_data, current_user.id)
    
    # Broadcast reply
    await manager.broadcast_to_document(
        reply.document_id,
        {
            "type": "annotation_reply",
            "annotation": reply.dict(),
            "parentId": str(annotation_id),
            "userId": current_user.id
        }
    )
    
    return reply
```

### 5. WebSocket Manager (backend/app/core/websocket.py)
```python
import socketio
from typing import Dict, Set
import json

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio)

class ConnectionManager:
    def __init__(self):
        # Track active connections by document ID
        self.document_connections: Dict[int, Set[str]] = {}
        # Track user sessions
        self.user_sessions: Dict[str, str] = {}
    
    async def connect(self, sid: str, user_id: str):
        """Handle new WebSocket connection."""
        self.user_sessions[sid] = user_id
        await sio.emit('connected', {'message': 'Connected to annotation service'}, to=sid)
    
    async def disconnect(self, sid: str):
        """Handle WebSocket disconnection."""
        # Remove from all document rooms
        for doc_id, connections in self.document_connections.items():
            if sid in connections:
                connections.remove(sid)
        
        # Remove user session
        if sid in self.user_sessions:
            del self.user_sessions[sid]
    
    async def join_document(self, sid: str, document_id: int):
        """Join a document room for real-time updates."""
        if document_id not in self.document_connections:
            self.document_connections[document_id] = set()
        
        self.document_connections[document_id].add(sid)
        await sio.enter_room(sid, f"document_{document_id}")
        
        # Notify others in the document
        await self.broadcast_to_document(
            document_id,
            {
                "type": "user_joined",
                "userId": self.user_sessions.get(sid)
            },
            exclude_sid=sid
        )
    
    async def leave_document(self, sid: str, document_id: int):
        """Leave a document room."""
        if document_id in self.document_connections:
            self.document_connections[document_id].discard(sid)
        
        await sio.leave_room(sid, f"document_{document_id}")
        
        # Notify others
        await self.broadcast_to_document(
            document_id,
            {
                "type": "user_left",
                "userId": self.user_sessions.get(sid)
            }
        )
    
    async def broadcast_to_document(
        self, 
        document_id: int, 
        data: dict, 
        exclude_sid: str = None
    ):
        """Broadcast a message to all users viewing a document."""
        room = f"document_{document_id}"
        await sio.emit(
            'annotation_update',
            data,
            room=room,
            skip_sid=exclude_sid
        )
    
    async def send_to_user(self, user_id: str, event: str, data: dict):
        """Send a message to a specific user."""
        for sid, uid in self.user_sessions.items():
            if uid == user_id:
                await sio.emit(event, data, to=sid)

# Create global manager instance
manager = ConnectionManager()

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    if auth and 'token' in auth:
        # Validate token and get user ID
        user_id = validate_token(auth['token'])
        if user_id:
            await manager.connect(sid, user_id)
            return True
    return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    await manager.disconnect(sid)

@sio.event
async def join_document(sid, data):
    """Handle joining a document room."""
    document_id = data.get('documentId')
    if document_id:
        await manager.join_document(sid, document_id)

@sio.event
async def leave_document(sid, data):
    """Handle leaving a document room."""
    document_id = data.get('documentId')
    if document_id:
        await manager.leave_document(sid, document_id)

@sio.event
async def cursor_position(sid, data):
    """Share cursor position for collaborative features."""
    document_id = data.get('documentId')
    position = data.get('position')
    
    if document_id:
        await manager.broadcast_to_document(
            document_id,
            {
                "type": "cursor_update",
                "userId": manager.user_sessions.get(sid),
                "position": position
            },
            exclude_sid=sid
        )
```

### 6. Docker Compose for Development (docker-compose.yml)
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: annotation_user
      POSTGRES_PASSWORD: annotation_pass
      POSTGRES_DB: annotation_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://annotation_user:annotation_pass@postgres:5432/annotation_db
      REDIS_URL: redis://redis:6379
      SECRET_KEY: your-secret-key-here
      OAUTH_CLIENT_ID: ${OAUTH_CLIENT_ID}
      OAUTH_CLIENT_SECRET: ${OAUTH_CLIENT_SECRET}
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      REACT_APP_API_URL: http://localhost:8000/api
      REACT_APP_WS_URL: ws://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    command: npm start

volumes:
  postgres_data:
```

## Environment Configuration

### Frontend (.env)
```bash
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_OAUTH_CLIENT_ID=your-oauth-client-id
REACT_APP_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

### Backend (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/annotation_db

# Redis for caching and sessions
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Configuration
OAUTH_PROVIDER=google  # or azure, okta
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# For Google
GOOGLE_DOMAIN=yourcompany.com

# For Azure
AZURE_TENANT_ID=your-tenant-id

# For Okta
OKTA_DOMAIN=yourcompany.okta.com

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]

# File Storage (local or S3)
STORAGE_TYPE=local  # or s3
UPLOAD_PATH=./uploads

# S3 Configuration (if using S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_BUCKET_NAME=document-annotations
AWS_REGION=us-east-1
```

## Deployment Instructions

### Development Setup
```bash
# Clone the repository
git clone <your-repo>
cd document-annotation-system

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend
uvicorn main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm start
```

### Production Deployment

#### Using Docker
```bash
# Build and run with Docker Compose
docker-compose up --build

# For production, use docker-compose.prod.yml with:
# - Nginx reverse proxy
# - SSL certificates
# - Production database
# - Proper environment variables
```

#### Manual Deployment
1. **Backend**: Deploy to AWS ECS, Google Cloud Run, or Azure Container Instances
2. **Frontend**: Build and deploy to S3 + CloudFront, Vercel, or Netlify
3. **Database**: Use managed PostgreSQL (RDS, Cloud SQL, Azure Database)
4. **Redis**: Use managed Redis (ElastiCache, Cloud Memorystore)

## Testing Instructions

### Frontend Tests
```bash
cd frontend
npm test
npm run test:e2e  # End-to-end tests with Cypress
```

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app  # With coverage
```

## Features Checklist

### Phase 1: Core Annotation Features
- [ ] User authentication with OAuth
- [ ] Document upload and viewing (HTML/Markdown)
- [ ] Text selection and annotation
- [ ] Highlight with colors
- [ ] Comment on selected text
- [ ] View all annotations in sidebar
- [ ] Delete own annotations

### Phase 2: Advanced Features
- [ ] PDF support with PDF.js
- [ ] Annotation threading/replies
- [ ] Resolve/unresolve annotations
- [ ] Filter annotations by user/status
- [ ] Search within annotations
- [ ] Export annotations

### Phase 3: Collaboration
- [ ] Real-time annotation updates
- [ ] User presence indicators
- [ ] Cursor position sharing
- [ ] Annotation notifications
- [ ] Version history
- [ ] Annotation permissions

### Phase 4: Enterprise Features
- [ ] Admin dashboard
- [ ] Bulk document upload
- [ ] Annotation analytics
- [ ] API for external integrations
- [ ] Audit logs
- [ ] Custom annotation types

## Troubleshooting Guide

### Common Issues

1. **CORS Errors**
   - Check CORS_ORIGINS in backend .env
   - Ensure frontend URL is in allowed origins

2. **WebSocket Connection Failed**
   - Verify WebSocket URL in frontend .env
   - Check firewall/proxy settings
   - Ensure Socket.IO versions match

3. **Annotations Not Saving**
   - Check database connection
   - Verify user has permission
   - Look for errors in browser console

4. **PDF Rendering Issues**
   - Ensure PDF.js worker is loaded
   - Check CORS for PDF files
   - Verify PDF file format

5. **OAuth Login Failed**
   - Verify redirect URI matches exactly
   - Check client ID and secret
   - Ensure scopes are approved

## Performance Optimization

1. **Frontend**
   - Lazy load documents
   - Virtual scrolling for long documents
   - Debounce annotation updates
   - Cache annotations locally

2. **Backend**
   - Use Redis for caching
   - Implement pagination
   - Database query optimization
   - Connection pooling

3. **WebSocket**
   - Throttle cursor updates
   - Batch annotation updates
   - Implement reconnection logic

## Security Considerations

1. **Authentication**
   - Implement JWT refresh tokens
   - Session timeout
   - Rate limiting

2. **Authorization**
   - Document-level permissions
   - Annotation edit/delete permissions
   - Admin roles

3. **Data Protection**
   - Encrypt sensitive data
   - SQL injection prevention
   - XSS protection
   - CSRF tokens

## Next Steps

1. **Immediate Priorities**
   - Get basic annotation working
   - Implement OAuth login
   - Deploy to staging environment

2. **Short Term**
   - Add PDF support
   - Implement real-time updates
   - Add annotation search

3. **Long Term**
   - Machine learning for smart annotations
   - Integration with document management systems
   - Mobile applications
   - API for third-party integrations