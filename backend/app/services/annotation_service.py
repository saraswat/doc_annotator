from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from fastapi import HTTPException
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.models import Annotation, User, Document
from app.schemas.annotation import (
    AnnotationCreate, 
    AnnotationUpdate, 
    AnnotationResponse,
    AnnotationWithReplies
)

class AnnotationService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_annotation(
        self, 
        annotation_data: AnnotationCreate, 
        user_id: int
    ) -> AnnotationResponse:
        """Create a new annotation"""
        
        # Verify document exists and user has access
        await self.check_document_access(annotation_data.document_id, user_id)
        
        # Create annotation
        annotation = Annotation(
            document_id=annotation_data.document_id,
            user_id=user_id,
            target=annotation_data.target.dict(),
            body=annotation_data.body.dict(),
            reply_to=annotation_data.reply_to,
            page_number=annotation_data.page_number
        )
        
        # Set thread_id for threading
        if annotation_data.reply_to:
            parent_result = await self.db.execute(
                select(Annotation).where(Annotation.id == annotation_data.reply_to)
            )
            parent = parent_result.scalar_one_or_none()
            if parent:
                annotation.thread_id = parent.thread_id or parent.id
        else:
            annotation.thread_id = None
        
        self.db.add(annotation)
        await self.db.commit()
        await self.db.refresh(annotation)
        
        # Get user info for response
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one()
        
        return AnnotationResponse(
            id=annotation.id,
            document_id=annotation.document_id,
            user_id=annotation.user_id,
            target=annotation.target,
            body=annotation.body,
            reply_to=annotation.reply_to,
            thread_id=annotation.thread_id,
            resolved=annotation.resolved,
            resolved_by=annotation.resolved_by,
            resolved_at=annotation.resolved_at,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            page_number=annotation.page_number,
            user_name=user.name,
            user_avatar=user.avatar_url,
            can_edit=(user_id == annotation.user_id),
            can_delete=(user_id == annotation.user_id)
        )
    
    async def get_annotation(self, annotation_id: UUID) -> Optional[Annotation]:
        """Get annotation by ID"""
        result = await self.db.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        return result.scalar_one_or_none()
    
    async def get_document_annotations(
        self,
        document_id: int,
        include_resolved: bool = True,
        page_number: Optional[int] = None
    ) -> List[AnnotationWithReplies]:
        """Get all annotations for a document with replies"""
        
        # Build query for top-level annotations (not replies)
        query = select(Annotation, User).join(User, Annotation.user_id == User.id).where(
            and_(
                Annotation.document_id == document_id,
                Annotation.reply_to.is_(None)
            )
        )
        
        if not include_resolved:
            query = query.where(Annotation.resolved == False)
        
        if page_number is not None:
            query = query.where(Annotation.page_number == page_number)
        
        query = query.order_by(Annotation.created_at.desc())
        
        result = await self.db.execute(query)
        annotations_with_users = result.all()
        
        # Build response with replies
        response_annotations = []
        for annotation, user in annotations_with_users:
            # Get replies for this annotation
            replies = await self._get_annotation_replies(annotation.id)
            
            annotation_response = AnnotationWithReplies(
                id=annotation.id,
                document_id=annotation.document_id,
                user_id=annotation.user_id,
                target=annotation.target,
                body=annotation.body,
                reply_to=annotation.reply_to,
                thread_id=annotation.thread_id,
                resolved=annotation.resolved,
                resolved_by=annotation.resolved_by,
                resolved_at=annotation.resolved_at,
                created_at=annotation.created_at,
                updated_at=annotation.updated_at,
                page_number=annotation.page_number,
                user_name=user.name,
                user_avatar=user.avatar_url,
                can_edit=True,  # TODO: Check permissions
                can_delete=True,  # TODO: Check permissions
                replies=replies
            )
            
            response_annotations.append(annotation_response)
        
        return response_annotations
    
    async def _get_annotation_replies(self, parent_id: UUID) -> List[AnnotationResponse]:
        """Get replies for an annotation"""
        query = select(Annotation, User).join(User, Annotation.user_id == User.id).where(
            Annotation.reply_to == parent_id
        ).order_by(Annotation.created_at.asc())
        
        result = await self.db.execute(query)
        replies_with_users = result.all()
        
        replies = []
        for reply, user in replies_with_users:
            reply_response = AnnotationResponse(
                id=reply.id,
                document_id=reply.document_id,
                user_id=reply.user_id,
                target=reply.target,
                body=reply.body,
                reply_to=reply.reply_to,
                thread_id=reply.thread_id,
                resolved=reply.resolved,
                resolved_by=reply.resolved_by,
                resolved_at=reply.resolved_at,
                created_at=reply.created_at,
                updated_at=reply.updated_at,
                page_number=reply.page_number,
                user_name=user.name,
                user_avatar=user.avatar_url,
                can_edit=True,  # TODO: Check permissions
                can_delete=True  # TODO: Check permissions
            )
            replies.append(reply_response)
        
        return replies
    
    async def update_annotation(
        self, 
        annotation_id: UUID, 
        update_data: AnnotationUpdate
    ) -> AnnotationResponse:
        """Update an annotation"""
        
        result = await self.db.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()
        
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        # Update fields
        update_data_dict = update_data.dict(exclude_unset=True)
        for field, value in update_data_dict.items():
            if field == "body":
                annotation.body = value.dict()
            else:
                setattr(annotation, field, value)
        
        annotation.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(annotation)
        
        # Get user info for response
        user_result = await self.db.execute(
            select(User).where(User.id == annotation.user_id)
        )
        user = user_result.scalar_one()
        
        return AnnotationResponse(
            id=annotation.id,
            document_id=annotation.document_id,
            user_id=annotation.user_id,
            target=annotation.target,
            body=annotation.body,
            reply_to=annotation.reply_to,
            thread_id=annotation.thread_id,
            resolved=annotation.resolved,
            resolved_by=annotation.resolved_by,
            resolved_at=annotation.resolved_at,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            page_number=annotation.page_number,
            user_name=user.name,
            user_avatar=user.avatar_url,
            can_edit=True,
            can_delete=True
        )
    
    async def delete_annotation(self, annotation_id: UUID):
        """Delete an annotation"""
        
        result = await self.db.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()
        
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        # Delete all replies first
        await self.db.execute(
            select(Annotation).where(Annotation.reply_to == annotation_id)
        )
        
        await self.db.delete(annotation)
        await self.db.commit()
    
    async def resolve_annotation(
        self, 
        annotation_id: UUID, 
        resolved_by: int
    ) -> AnnotationResponse:
        """Mark annotation as resolved"""
        
        result = await self.db.execute(
            select(Annotation).where(Annotation.id == annotation_id)
        )
        annotation = result.scalar_one_or_none()
        
        if not annotation:
            raise HTTPException(status_code=404, detail="Annotation not found")
        
        annotation.resolved = True
        annotation.resolved_by = resolved_by
        annotation.resolved_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(annotation)
        
        # Get user info for response
        user_result = await self.db.execute(
            select(User).where(User.id == annotation.user_id)
        )
        user = user_result.scalar_one()
        
        return AnnotationResponse(
            id=annotation.id,
            document_id=annotation.document_id,
            user_id=annotation.user_id,
            target=annotation.target,
            body=annotation.body,
            reply_to=annotation.reply_to,
            thread_id=annotation.thread_id,
            resolved=annotation.resolved,
            resolved_by=annotation.resolved_by,
            resolved_at=annotation.resolved_at,
            created_at=annotation.created_at,
            updated_at=annotation.updated_at,
            page_number=annotation.page_number,
            user_name=user.name,
            user_avatar=user.avatar_url,
            can_edit=True,
            can_delete=True
        )
    
    async def check_document_access(self, document_id: int, user_id: int):
        """Check if user has access to document"""
        
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        if document.owner_id != user_id and not document.is_public:
            raise HTTPException(
                status_code=403, 
                detail="Not authorized to access this document"
            )