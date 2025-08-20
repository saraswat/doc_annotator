from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from uuid import UUID
import json
import logging
from datetime import datetime

from app.core.database import get_async_session
from app.core.security import get_current_user
from app.models import User
from app.models.chat import ChatSession, ChatMessage, ChatContext, MessageFeedback
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    MessageFeedbackCreate,
    MessageFeedbackResponse,
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
    await db.commit()  # Commit first to generate session.id
    await db.refresh(session)  # Refresh to get the generated ID
    
    # Create initial context with the now-available session.id
    context = ChatContext(session_id=session.id)
    db.add(context)
    
    await db.commit()
    await db.refresh(context)
    
    # Return manually constructed response to avoid lazy loading issues
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        status=session.status,
        session_metadata=session.session_metadata or {},
        settings=session.settings or {},
        message_count=session.message_count,
        total_tokens=session.total_tokens,
        messages=None  # No messages for new session
    )

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
    
    # Convert to response format manually to avoid lazy loading issues
    return [
        ChatSessionResponse(
            id=session.id,
            user_id=session.user_id,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            status=session.status,
            session_metadata=session.session_metadata or {},
            settings=session.settings or {},
            message_count=session.message_count,
            total_tokens=session.total_tokens,
            messages=None  # Don't load messages for list view
        )
        for session in sessions
    ]

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
            ChatSession.id == str(session_id),
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == str(session_id))
        .order_by(ChatMessage.timestamp)
    )
    messages = result.scalars().all()
    
    # Convert to response format manually to avoid lazy loading issues
    return ChatSessionResponse(
        id=session.id,
        user_id=session.user_id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        status=session.status,
        session_metadata=session.session_metadata or {},
        settings=session.settings or {},
        message_count=session.message_count,
        total_tokens=session.total_tokens,
        messages=[
            ChatMessageResponse(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp,
                tokens=msg.tokens,
                model=msg.model,
                message_metadata=msg.message_metadata or {},
                document_references=msg.document_references or [],
                annotation_references=msg.annotation_references or []
            ) for msg in messages
        ]
    )

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
            ChatSession.id == str(session_id),
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Stream LLM response
    async def generate():
        try:
            from app.services.llm_client import get_llm_client
            
            # Save user message
            user_message = ChatMessage(
                session_id=str(session_id),
                role="user",
                content=message_data.content,
                model=message_data.settings.model
            )
            db.add(user_message)
            await db.commit()
            await db.refresh(user_message)
            
            # Get recent messages for context
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == str(session_id))
                .order_by(ChatMessage.timestamp.desc())
                .limit(20)
            )
            recent_messages = list(reversed(result.scalars().all()))
            
            # Build conversation for LLM
            conversation = []
            
            # Add system prompt
            conversation.append({
                "role": "system",
                "content": "You are a helpful AI assistant. Provide clear, accurate, and helpful responses."
            })
            
            # Add recent messages (excluding the just-added user message to avoid duplication)
            for msg in recent_messages[:-1]:
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            conversation.append({
                "role": "user",
                "content": message_data.content
            })
            
            # Get LLM client and stream response
            llm_client = await get_llm_client()
            full_response = ""
            assistant_message = None
            
            async for chunk in llm_client.chat_completion(
                messages=conversation,
                model=message_data.settings.model,
                temperature=message_data.settings.temperature,
                max_tokens=message_data.settings.maxTokens,
                stream=True
            ):
                if chunk.type == "chunk":
                    full_response += chunk.content
                    # Stream chunk to frontend
                    chunk_data = {
                        'type': 'chunk',
                        'content': chunk.content
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    
                elif chunk.type == "complete":
                    # Save assistant message to database
                    assistant_message = ChatMessage(
                        session_id=str(session_id),
                        role="assistant",
                        content=full_response,
                        model=message_data.settings.model,
                        tokens=(
                            chunk.metadata.get("usage", {}).get("output_tokens") 
                            if chunk.metadata and chunk.metadata.get("usage") 
                            else len(full_response.split())
                        )
                    )
                    db.add(assistant_message)
                    
                    # Update session stats
                    session.message_count += 2  # user + assistant
                    session.updated_at = datetime.utcnow()
                    
                    await db.commit()
                    await db.refresh(assistant_message)
                    
                    # Final completion message
                    completion = {
                        'type': 'complete',
                        'messageId': str(assistant_message.id),
                        'content': chunk.content if chunk.content else "",
                        'tokens': assistant_message.tokens or len(full_response.split())
                    }
                    yield f"data: {json.dumps(completion)}\n\n"
                    break
                    
                elif chunk.type == "error":
                    error_chunk = {
                        'type': 'error',
                        'error': chunk.error
                    }
                    yield f"data: {json.dumps(error_chunk)}\n\n"
                    break
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in chat streaming: {str(e)}")
            error_chunk = {
                'type': 'error',
                'error': f"Internal server error: {str(e)}"
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
            ChatSession.id == str(session_id),
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get context
    result = await db.execute(
        select(ChatContext).where(ChatContext.session_id == str(session_id))
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
            ChatSession.id == str(session_id),
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get context
    result = await db.execute(
        select(ChatContext).where(ChatContext.session_id == str(session_id))
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
            ChatSession.id == str(session_id),
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    
    return {"status": "deleted"}

@router.post("/messages/{message_id}/feedback", response_model=MessageFeedbackResponse)
async def submit_message_feedback(
    message_id: UUID,
    feedback_data: MessageFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Submit feedback for a specific message."""
    # First verify the message exists and belongs to the user
    result = await db.execute(
        select(ChatMessage)
        .join(ChatSession)
        .where(
            ChatMessage.id == str(message_id),
            ChatSession.user_id == current_user.id,
            ChatMessage.role == "assistant"  # Only allow feedback on assistant messages
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or not eligible for feedback")
    
    # Check if feedback already exists for this message
    existing_feedback_result = await db.execute(
        select(MessageFeedback).where(MessageFeedback.message_id == str(message_id))
    )
    existing_feedback = existing_feedback_result.scalar_one_or_none()
    
    if existing_feedback:
        # Update existing feedback
        existing_feedback.feedback_type = feedback_data.feedback_type
        existing_feedback.updated_at = datetime.utcnow()
        feedback = existing_feedback
    else:
        # Create new feedback
        feedback = MessageFeedback(
            message_id=str(message_id),
            session_id=message.session_id,
            user_id=current_user.id,
            feedback_type=feedback_data.feedback_type,
            message_order=feedback_data.message_order
        )
        db.add(feedback)
    
    await db.commit()
    await db.refresh(feedback)
    
    return MessageFeedbackResponse(
        id=feedback.id,
        message_id=feedback.message_id,
        session_id=feedback.session_id,
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        message_order=feedback.message_order,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )

@router.get("/messages/{message_id}/feedback", response_model=Optional[MessageFeedbackResponse])
async def get_message_feedback(
    message_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get feedback for a specific message."""
    # Verify the message exists and belongs to the user
    result = await db.execute(
        select(ChatMessage)
        .join(ChatSession)
        .where(
            ChatMessage.id == str(message_id),
            ChatSession.user_id == current_user.id
        )
    )
    message = result.scalar_one_or_none()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # Get feedback
    feedback_result = await db.execute(
        select(MessageFeedback).where(MessageFeedback.message_id == str(message_id))
    )
    feedback = feedback_result.scalar_one_or_none()
    
    if not feedback:
        return None
    
    return MessageFeedbackResponse(
        id=feedback.id,
        message_id=feedback.message_id,
        session_id=feedback.session_id,
        user_id=feedback.user_id,
        feedback_type=feedback.feedback_type,
        message_order=feedback.message_order,
        created_at=feedback.created_at,
        updated_at=feedback.updated_at
    )