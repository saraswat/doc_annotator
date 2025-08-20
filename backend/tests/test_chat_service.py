import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.chat_service import ChatService
from app.models.chat import ChatSession, ChatMessage, ChatContext
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatSettings, StreamingResponse


@pytest.fixture
def mock_db_session():
    """Mock database session for testing"""
    session = Mock(spec=AsyncSession)
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def mock_context_manager():
    """Mock context manager for testing"""
    context_manager = Mock()
    context_manager.update_from_conversation = AsyncMock()
    return context_manager


@pytest.fixture
def sample_chat_session():
    """Sample chat session for testing"""
    return ChatSession(
        id=str(uuid4()),
        user_id=1,
        title="Test Session",
        status="active",
        session_metadata={},
        settings={},
        message_count=0,
        total_tokens=0
    )


@pytest.fixture
def sample_chat_message():
    """Sample chat message for testing"""
    return ChatMessage(
        id=str(uuid4()),
        session_id=str(uuid4()),
        role="user",
        content="Test message",
        message_metadata={}
    )


class TestChatService:
    """Test cases for ChatService"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, mock_db_session, mock_context_manager):
        """Test creating a new chat session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        session_data = ChatSessionCreate(title="Test Session")
        
        result = await service.create_session(user_id=1, session_data=session_data)
        
        assert result.user_id == 1
        assert result.title == "Test Session"
        assert result.status == "active"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_exists(self, mock_db_session, mock_context_manager, sample_chat_session):
        """Test getting an existing chat session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db_session.execute.return_value = mock_result
        
        result = await service.get_session(sample_chat_session.id, user_id=1)
        
        assert result == sample_chat_session
        mock_db_session.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_not_exists(self, mock_db_session, mock_context_manager):
        """Test getting a non-existent chat session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result
        
        result = await service.get_session("non-existent-id", user_id=1)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_add_message(self, mock_db_session, mock_context_manager, sample_chat_session):
        """Test adding a message to a chat session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock get_session to return our sample session
        with patch.object(service, 'get_session', return_value=sample_chat_session):
            message_data = ChatMessageCreate(
                content="Test message",
                settings=ChatSettings(),
                context_options={}
            )
            
            result = await service.add_message(
                session_id=sample_chat_session.id,
                user_id=1,
                message_data=message_data
            )
            
            assert result.content == "Test message"
            assert result.role == "user"
            assert result.session_id == sample_chat_session.id
            mock_db_session.add.assert_called()
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_message_session_not_found(self, mock_db_session, mock_context_manager):
        """Test adding a message when session doesn't exist"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock get_session to return None
        with patch.object(service, 'get_session', return_value=None):
            message_data = ChatMessageCreate(
                content="Test message",
                settings=ChatSettings(),
                context_options={}
            )
            
            with pytest.raises(ValueError, match="Session .* not found or access denied"):
                await service.add_message("non-existent-id", 1, message_data)
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, mock_db_session, mock_context_manager):
        """Test listing chat sessions for a user"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        sessions = [
            ChatSession(id="1", user_id=1, title="Session 1"),
            ChatSession(id="2", user_id=1, title="Session 2")
        ]
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = sessions
        mock_db_session.execute.return_value = mock_result
        
        result = await service.list_sessions(user_id=1)
        
        assert len(result) == 2
        assert result[0].title == "Session 1"
        assert result[1].title == "Session 2"
    
    @pytest.mark.asyncio
    async def test_delete_session(self, mock_db_session, mock_context_manager, sample_chat_session):
        """Test deleting a chat session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock get_session to return our sample session
        with patch.object(service, 'get_session', return_value=sample_chat_session):
            result = await service.delete_session(sample_chat_session.id, user_id=1)
            
            assert result is True
            mock_db_session.delete.assert_called_once_with(sample_chat_session)
            mock_db_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, mock_db_session, mock_context_manager):
        """Test deleting a non-existent session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock get_session to return None
        with patch.object(service, 'get_session', return_value=None):
            result = await service.delete_session("non-existent-id", user_id=1)
            
            assert result is False
            mock_db_session.delete.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_session_messages(self, mock_db_session, mock_context_manager):
        """Test getting messages for a session"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        messages = [
            ChatMessage(id="1", session_id="session-1", role="user", content="Hello"),
            ChatMessage(id="2", session_id="session-1", role="assistant", content="Hi there!")
        ]
        
        # Mock database query result
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = messages
        mock_db_session.execute.return_value = mock_result
        
        result = await service.get_session_messages("session-1", user_id=1)
        
        assert len(result) == 2
        assert result[0].content == "Hello"
        assert result[1].content == "Hi there!"
    
    @pytest.mark.asyncio
    async def test_build_system_prompt(self, mock_db_session, mock_context_manager):
        """Test building system prompt from context"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        context = ChatContext(
            session_id="test-session",
            problem_summary="Working on a coding problem",
            current_goal="Fix the bug in the authentication system",
            tasks=[
                {"description": "Review the login code", "status": "pending"},
                {"description": "Test the fix", "status": "pending"}
            ]
        )
        
        context_options = {
            "document_ids": ["doc1", "doc2"],
            "enable_web_browsing": True,
            "enable_deep_research": True
        }
        
        result = await service._build_system_prompt(context, context_options)
        
        assert "Working on a coding problem" in result
        assert "Fix the bug in the authentication system" in result
        assert "Review the login code" in result
        assert "Test the fix" in result
        assert "web browsing" in result
        assert "deep research" in result
        assert "documents" in result
    
    @pytest.mark.asyncio
    async def test_stream_chat_response_session_not_found(self, mock_db_session, mock_context_manager):
        """Test streaming response when session is not found"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock get_session to return None
        with patch.object(service, 'get_session', return_value=None):
            message_data = ChatMessageCreate(
                content="Test message",
                settings=ChatSettings(),
                context_options={}
            )
            
            response_generator = service.stream_chat_response("non-existent", 1, message_data)
            responses = []
            
            async for response in response_generator:
                responses.append(response)
            
            assert len(responses) == 1
            assert responses[0].type == "error"
            assert "not found" in responses[0].error
    
    @pytest.mark.asyncio
    async def test_update_session_context(self, mock_db_session, mock_context_manager):
        """Test updating session context"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Create a mock context
        existing_context = ChatContext(
            session_id="test-session",
            problem_summary="Original summary",
            current_goal="Original goal"
        )
        
        # Mock get_session_context to return existing context
        with patch.object(service, 'get_session_context', return_value=existing_context):
            from app.schemas.chat import ChatContextUpdate
            
            updates = ChatContextUpdate(
                problem_summary="Updated summary",
                current_goal="Updated goal"
            )
            
            result = await service.update_session_context("test-session", 1, updates)
            
            assert result.problem_summary == "Updated summary"
            assert result.current_goal == "Updated goal"
            mock_db_session.commit.assert_called_once()


class TestChatServiceStreaming:
    """Test cases for ChatService streaming functionality"""
    
    @pytest.mark.asyncio
    async def test_stream_chat_response_success(self, mock_db_session, mock_context_manager, sample_chat_session):
        """Test successful streaming chat response"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Mock dependencies
        with patch.object(service, 'get_session', return_value=sample_chat_session), \
             patch.object(service, 'add_message', return_value=Mock()), \
             patch.object(service, 'get_session_messages', return_value=[]), \
             patch('app.services.chat_service.get_llm_client') as mock_get_client:
            
            # Mock LLM client response
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client
            
            # Create a mock streaming response
            async def mock_chat_completion(*args, **kwargs):
                yield StreamingResponse(type="chunk", content="Hello")
                yield StreamingResponse(type="chunk", content=" world!")
                yield StreamingResponse(type="complete", content="", metadata={"usage": {}})
            
            mock_client.chat_completion = mock_chat_completion
            
            message_data = ChatMessageCreate(
                content="Test message",
                settings=ChatSettings(model="gpt-4"),
                context_options={}
            )
            
            responses = []
            async for response in service.stream_chat_response(sample_chat_session.id, 1, message_data):
                responses.append(response)
            
            assert len(responses) >= 3  # At least chunk + chunk + complete
            assert any(r.type == "chunk" and r.content == "Hello" for r in responses)
            assert any(r.type == "chunk" and r.content == " world!" for r in responses)
            assert any(r.type == "complete" for r in responses)


@pytest.mark.asyncio
class TestChatServiceIntegration:
    """Integration tests for ChatService with real database operations"""
    
    async def test_full_conversation_flow(self, mock_db_session, mock_context_manager):
        """Test a complete conversation flow from creation to deletion"""
        service = ChatService(mock_db_session, mock_context_manager)
        
        # Test session creation
        session_data = ChatSessionCreate(title="Integration Test")
        session = await service.create_session(user_id=1, session_data=session_data)
        
        assert session.title == "Integration Test"
        
        # Test adding messages
        user_message = ChatMessageCreate(
            content="Hello, can you help me with coding?",
            settings=ChatSettings(),
            context_options={}
        )
        
        with patch.object(service, 'get_session', return_value=session):
            message = await service.add_message(session.id, 1, user_message)
            assert message.content == "Hello, can you help me with coding?"
            
        # Test session update
        with patch.object(service, 'get_session', return_value=session):
            from app.schemas.chat import ChatSessionUpdate
            updated_session = await service.update_session(
                session.id, 1, 
                ChatSessionUpdate(title="Updated Test Session")
            )
            assert updated_session.title == "Updated Test Session"