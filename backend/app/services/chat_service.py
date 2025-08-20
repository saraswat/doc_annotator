from typing import List, Dict, Any, Optional, AsyncGenerator
import logging
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, and_

from ..models.chat import ChatSession, ChatMessage, ChatContext
from ..schemas.chat import (
    ChatSessionCreate, ChatSessionUpdate, ChatMessageCreate, 
    StreamingResponse, ChatContextUpdate
)
from .llm_client import get_llm_client
from .context_manager import ContextManager

logger = logging.getLogger(__name__)

class ChatService:
    """Service for managing chat sessions and AI interactions"""
    
    def __init__(self, db: AsyncSession, context_manager: Optional[ContextManager] = None):
        self.db = db
        self.context_manager = context_manager or ContextManager()
    
    async def create_session(
        self, 
        user_id: int, 
        session_data: ChatSessionCreate
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            user_id=user_id,
            title=session_data.title or "New Chat",
            status=session_data.status or "active",
            metadata=session_data.metadata or {}
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        logger.info(f"Created chat session {session.id} for user {user_id}")
        return session
    
    async def get_session(
        self, 
        session_id: UUID, 
        user_id: int
    ) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        result = await self.db.execute(
            select(ChatSession)
            .options(
                selectinload(ChatSession.messages),
                selectinload(ChatSession.context)
            )
            .where(
                and_(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def list_sessions(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[ChatSession]:
        """List chat sessions for a user"""
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def update_session(
        self,
        session_id: UUID,
        user_id: int,
        updates: ChatSessionUpdate
    ) -> Optional[ChatSession]:
        """Update a chat session"""
        session = await self.get_session(session_id, user_id)
        if not session:
            return None
        
        for field, value in updates.dict(exclude_unset=True).items():
            setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def delete_session(
        self, 
        session_id: UUID, 
        user_id: int
    ) -> bool:
        """Delete a chat session"""
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        
        await self.db.delete(session)
        await self.db.commit()
        
        logger.info(f"Deleted chat session {session_id}")
        return True
    
    async def get_session_messages(
        self,
        session_id: UUID,
        user_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get messages for a chat session"""
        result = await self.db.execute(
            select(ChatMessage)
            .join(ChatSession)
            .where(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatSession.user_id == user_id
                )
            )
            .order_by(ChatMessage.timestamp)
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()
    
    async def add_message(
        self,
        session_id: UUID,
        user_id: int,
        message_data: ChatMessageCreate
    ) -> ChatMessage:
        """Add a message to a chat session"""
        # Verify session exists and belongs to user
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or access denied")
        
        message = ChatMessage(
            session_id=session_id,
            role=message_data.role,
            content=message_data.content,
            metadata=message_data.metadata or {}
        )
        
        self.db.add(message)
        
        # Update session metadata
        session.last_message = message_data.content[:100] + "..." if len(message_data.content) > 100 else message_data.content
        session.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def stream_chat_response(
        self,
        session_id: UUID,
        user_id: int,
        message_data: ChatMessageCreate,
        context_options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[StreamingResponse, None]:
        """Stream AI response for a chat message"""
        try:
            # Verify session and add user message
            session = await self.get_session(session_id, user_id)
            if not session:
                yield StreamingResponse(
                    type="error",
                    content="",
                    error="Session not found or access denied"
                )
                return
            
            # Add user message to database
            user_message = await self.add_message(session_id, user_id, message_data)
            
            # Get recent conversation history
            recent_messages = await self.get_session_messages(
                session_id, user_id, limit=20
            )
            
            # Build conversation for LLM
            conversation = []
            
            # Add system context if available
            if session.context:
                system_prompt = await self._build_system_prompt(
                    session.context, context_options
                )
                if system_prompt:
                    conversation.append({
                        "role": "system",
                        "content": system_prompt
                    })
            
            # Add recent messages
            for msg in recent_messages[:-1]:  # Exclude the just-added user message
                conversation.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current user message
            conversation.append({
                "role": "user",
                "content": message_data.content
            })
            
            # Get LLM settings from message metadata
            settings = message_data.settings
            model = settings.model if settings else "gpt-4"
            temperature = settings.temperature if settings else 0.7
            max_tokens = settings.max_tokens if settings else 2000
            
            # Get LLM client and stream response
            llm_client = await get_llm_client()
            full_response = ""
            
            async for chunk in llm_client.chat_completion(
                messages=conversation,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            ):
                if chunk.type == "chunk":
                    full_response += chunk.content
                    yield chunk
                elif chunk.type == "complete":
                    # Save assistant message to database
                    assistant_message = ChatMessage(
                        session_id=session_id,
                        role="assistant",
                        content=full_response,
                        metadata={
                            "model": model,
                            "settings": settings,
                            "usage": chunk.metadata.get("usage") if chunk.metadata else None
                        }
                    )
                    
                    self.db.add(assistant_message)
                    
                    # Update session
                    session.last_message = full_response[:100] + "..." if len(full_response) > 100 else full_response
                    session.message_count = len(recent_messages) + 1  # +1 for the assistant message
                    session.updated_at = datetime.utcnow()
                    
                    await self.db.commit()
                    await self.db.refresh(assistant_message)
                    
                    # Update context based on conversation
                    if context_options and context_options.get("enable_context_updates", True):
                        await self._update_context_from_conversation(
                            session, user_message.content, full_response
                        )
                    
                    # Yield completion with message ID
                    yield StreamingResponse(
                        type="complete",
                        content=chunk.content,
                        message_id=str(assistant_message.id),
                        metadata=chunk.metadata
                    )
                    break
                elif chunk.type == "error":
                    yield chunk
                    break
        
        except Exception as e:
            logger.error(f"Error streaming chat response: {str(e)}")
            yield StreamingResponse(
                type="error",
                content="",
                error=f"Internal server error: {str(e)}"
            )
    
    async def _build_system_prompt(
        self, 
        context: ChatContext, 
        context_options: Optional[Dict[str, Any]]
    ) -> str:
        """Build system prompt from context and options"""
        prompt_parts = []
        
        # Base system prompt
        prompt_parts.append(
            "You are a helpful AI assistant. Provide clear, accurate, and contextual responses."
        )
        
        # Add problem context
        if context.problem_summary:
            prompt_parts.append(f"\nCurrent Problem Context:\n{context.problem_summary}")
        
        if context.current_goal:
            prompt_parts.append(f"\nCurrent Goal: {context.current_goal}")
        
        # Add task context
        if context.tasks:
            active_tasks = [
                task for task in context.tasks 
                if task.get("status") != "completed"
            ]
            if active_tasks:
                task_list = "\n".join([
                    f"- {task.get('description', '')}" 
                    for task in active_tasks
                ])
                prompt_parts.append(f"\nActive Tasks:\n{task_list}")
        
        # Add document context if provided
        if context_options and context_options.get("document_ids"):
            prompt_parts.append(
                "\nYou have access to specific documents in this conversation. "
                "Reference them when relevant to provide accurate information."
            )
        
        # Add capabilities based on settings
        capabilities = []
        if context_options and context_options.get("enable_web_browsing"):
            capabilities.append("web browsing for current information")
        if context_options and context_options.get("enable_deep_research"):
            capabilities.append("deep research and analysis")
        
        if capabilities:
            prompt_parts.append(f"\nAvailable capabilities: {', '.join(capabilities)}")
        
        return "\n".join(prompt_parts)
    
    async def _update_context_from_conversation(
        self,
        session: ChatSession,
        user_message: str,
        assistant_response: str
    ) -> None:
        """Update session context based on conversation"""
        try:
            if not session.context:
                # Create new context
                context = ChatContext(
                    session_id=session.id,
                    problem_summary="",
                    current_goal="",
                    tasks=[],
                    relevant_documents=[]
                )
                self.db.add(context)
                session.context = context
            
            # Use context manager to extract insights
            await self.context_manager.update_from_conversation(
                session.context, user_message, assistant_response
            )
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error updating context: {str(e)}")
    
    async def get_session_context(
        self, 
        session_id: UUID, 
        user_id: int
    ) -> Optional[ChatContext]:
        """Get context for a chat session"""
        result = await self.db.execute(
            select(ChatContext)
            .join(ChatSession)
            .where(
                and_(
                    ChatContext.session_id == session_id,
                    ChatSession.user_id == user_id
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def update_session_context(
        self,
        session_id: UUID,
        user_id: int,
        context_updates: ChatContextUpdate
    ) -> Optional[ChatContext]:
        """Update session context"""
        context = await self.get_session_context(session_id, user_id)
        if not context:
            # Create new context if it doesn't exist
            session = await self.get_session(session_id, user_id)
            if not session:
                return None
            
            context = ChatContext(
                session_id=session_id,
                problem_summary="",
                current_goal="",
                tasks=[],
                relevant_documents=[]
            )
            self.db.add(context)
        
        # Update context fields
        for field, value in context_updates.dict(exclude_unset=True).items():
            if hasattr(context, field):
                setattr(context, field, value)
        
        context.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(context)
        
        return context

def get_chat_service(db: AsyncSession) -> ChatService:
    """Dependency to get chat service instance"""
    return ChatService(db)