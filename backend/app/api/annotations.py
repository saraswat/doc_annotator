from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional
from uuid import UUID

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models import Annotation, User, Document
from app.schemas.annotation import (
    AnnotationCreate, 
    AnnotationUpdate, 
    AnnotationResponse,
    AnnotationWithReplies
)
from app.services.annotation_service import AnnotationService

router = APIRouter()

@router.post("/", response_model=AnnotationResponse)
@router.post("", response_model=AnnotationResponse)
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
    
    # TODO: Broadcast to WebSocket clients
    # await manager.broadcast_to_document(
    #     annotation.document_id,
    #     {
    #         "type": "annotation_created",
    #         "annotation": annotation.dict(),
    #         "userId": current_user.id
    #     }
    # )
    
    return annotation

@router.get("/document/{document_id}", response_model=List[AnnotationWithReplies])
@router.get("/document/{document_id}/", response_model=List[AnnotationWithReplies])
async def get_document_annotations(
    document_id: int,
    include_resolved: bool = Query(True),
    page_number: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all annotations for a document."""
    service = AnnotationService(db)
    
    # Check document access
    await service.check_document_access(document_id, current_user.id)
    
    annotations = await service.get_document_annotations(
        document_id,
        include_resolved=include_resolved,
        page_number=page_number
    )
    return annotations

@router.patch("/{annotation_id}", response_model=AnnotationResponse)
@router.patch("/{annotation_id}/", response_model=AnnotationResponse)
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
    
    # TODO: Broadcast update
    # await manager.broadcast_to_document(
    #     updated.document_id,
    #     {
    #         "type": "annotation_updated",
    #         "annotation": updated.dict(),
    #         "userId": current_user.id
    #     }
    # )
    
    return updated

@router.delete("/{annotation_id}")
@router.delete("/{annotation_id}/")
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
    
    # TODO: Broadcast deletion
    # await manager.broadcast_to_document(
    #     annotation.document_id,
    #     {
    #         "type": "annotation_deleted",
    #         "annotationId": str(annotation_id),
    #         "userId": current_user.id
    #     }
    # )
    
    return {"status": "deleted"}

@router.post("/{annotation_id}/resolve")
@router.post("/{annotation_id}/resolve/")
async def resolve_annotation(
    annotation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Mark an annotation as resolved."""
    service = AnnotationService(db)
    resolved = await service.resolve_annotation(annotation_id, current_user.id)
    
    # TODO: Broadcast resolution
    # await manager.broadcast_to_document(
    #     resolved.document_id,
    #     {
    #         "type": "annotation_resolved",
    #         "annotationId": str(annotation_id),
    #         "resolvedBy": current_user.id
    #     }
    # )
    
    return resolved

@router.post("/{annotation_id}/reply", response_model=AnnotationResponse)
@router.post("/{annotation_id}/reply/", response_model=AnnotationResponse)
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
    
    # TODO: Broadcast reply
    # await manager.broadcast_to_document(
    #     reply.document_id,
    #     {
    #         "type": "annotation_reply",
    #         "annotation": reply.dict(),
    #         "parentId": str(annotation_id),
    #         "userId": current_user.id
    #     }
    # )
    
    return reply