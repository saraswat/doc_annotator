from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
import json
from datetime import datetime

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models import User
from app.models.chat import ChatSession, ChatMessage, ChatContext
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ContextUpdate,
    ContextResponse
)

router = APIRouter()

@router.post("/sessions", response_model=ChatSessionResponse)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new chat session."""
    session = ChatSession(
        user_id=current_user.id,
        title=session_data.title or f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    db.add(session)
    
    # Create initial context
    context = ChatContext(session_id=session.id)
    db.add(context)
    
    await db.commit()
    await db.refresh(session)
    return session

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get user's chat sessions."""
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    
    if status:
        query = query.where(ChatSession.status == status)
    
    query = query.order_by(desc(ChatSession.updated_at)).offset(offset).limit(limit)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return sessions

@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get a specific chat session with messages."""
    # Get session
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.timestamp)
    )
    messages = result.scalars().all()
    
    # Convert to response format
    response_data = ChatSessionResponse.from_orm(session)
    response_data.messages = [ChatMessageResponse.from_orm(msg) for msg in messages]
    
    return response_data

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    message_data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Send a message and get streaming response."""
    # Verify session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # For now, create a simple echo response
    # In production, this would use the LLM client
    async def generate():
        try:
            # Save user message
            user_message = ChatMessage(
                session_id=session_id,
                role="user",
                content=message_data.content,
                model=message_data.settings.model
            )
            db.add(user_message)
            await db.commit()
            
            # Simple echo response for testing
            echo_response = f"Echo: {message_data.content}"
            
            # Save assistant message
            assistant_message = ChatMessage(
                session_id=session_id,
                role="assistant",
                content=echo_response,
                model=message_data.settings.model
            )
            db.add(assistant_message)
            
            # Update session stats
            session.message_count += 2
            session.updated_at = datetime.utcnow()
            await db.commit()
            
            # Stream response chunks
            for i, char in enumerate(echo_response):
                chunk = {
                    'type': 'chunk',
                    'content': char,
                    'message_id': str(assistant_message.id)
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Add small delay to simulate streaming
                import asyncio
                await asyncio.sleep(0.05)
            
            # Final completion message
            completion = {
                'type': 'complete',
                'message_id': str(assistant_message.id),
                'content': echo_response,
                'tokens': len(echo_response.split())
            }
            yield f"data: {json.dumps(completion)}\n\n"
            
        except Exception as e:
            error_chunk = {
                'type': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )

@router.get("/sessions/{session_id}/context", response_model=ContextResponse)
async def get_session_context(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get the current context for a session."""
    # Verify session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get context
    result = await db.execute(
        select(ChatContext).where(ChatContext.session_id == session_id)
    )
    context = result.scalar_one_or_none()
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return ContextResponse(
        session_id=context.session_id,
        summary=context.summary,
        current_goal=context.current_goal,
        tasks=context.tasks or [],
        relevant_documents=context.relevant_documents or [],
        updated_at=context.updated_at
    )

@router.patch("/sessions/{session_id}/context", response_model=ContextResponse)
async def update_session_context(
    session_id: UUID,
    context_update: ContextUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Manually update session context."""
    # Verify session ownership
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get context
    result = await db.execute(
        select(ChatContext).where(ChatContext.session_id == session_id)
    )
    context = result.scalar_one_or_none()
    
    if not context:
        raise HTTPException(status_code=404, detail="Context not found")
    
    # Update context
    update_data = context_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        if hasattr(context, key):
            setattr(context, key, value)
    
    context.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(context)
    
    return ContextResponse(
        session_id=context.session_id,
        summary=context.summary,
        current_goal=context.current_goal,
        tasks=context.tasks or [],
        relevant_documents=context.relevant_documents or [],
        updated_at=context.updated_at
    )

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    
    return {"status": "deleted"}