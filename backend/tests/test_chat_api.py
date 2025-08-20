import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, status
import json

from app.api.chat import router
from app.schemas.chat import ChatSessionCreate, ChatMessageCreate, ChatSettings, StreamingResponse
from app.models.chat import ChatSession, ChatMessage, ChatContext


@pytest.fixture
def app():
    """Create FastAPI app with chat router for testing"""
    app = FastAPI()
    app.include_router(router, prefix="/api/chat")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication"""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    return user


@pytest.fixture
def sample_session():
    """Sample chat session"""
    return ChatSession(
        id="test-session-id",
        user_id=1,
        title="Test Session",
        status="active",
        session_metadata={},
        settings={},
        message_count=0,
        total_tokens=0
    )


@pytest.fixture
def sample_message():
    """Sample chat message"""
    return ChatMessage(
        id="test-message-id",
        session_id="test-session-id",
        role="user",
        content="Hello, world!",
        message_metadata={}
    )


class TestChatSessionEndpoints:
    """Test cases for chat session endpoints"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_create_session_success(self, mock_get_service, mock_get_user, client, mock_current_user, sample_session):
        """Test successful session creation"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.create_session = AsyncMock(return_value=sample_session)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == "test-session-id"
        assert data["title"] == "Test Session"
        assert data["user_id"] == 1
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_create_session_without_title(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test session creation without title"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        default_session = ChatSession(
            id="new-session-id",
            user_id=1,
            title="New Chat",  # Default title
            status="active"
        )
        mock_service.create_session = AsyncMock(return_value=default_session)
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/chat/sessions",
            json={},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "New Chat"
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_sessions_success(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting user's chat sessions"""
        mock_get_user.return_value = mock_current_user
        
        sessions = [
            ChatSession(id="session-1", user_id=1, title="Session 1"),
            ChatSession(id="session-2", user_id=1, title="Session 2")
        ]
        
        mock_service = Mock()
        mock_service.list_sessions = AsyncMock(return_value=sessions)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Session 1"
        assert data[1]["title"] == "Session 2"
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_sessions_with_pagination(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting sessions with pagination parameters"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.list_sessions = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions?limit=10&offset=20",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        mock_service.list_sessions.assert_called_once_with(
            user_id=1, limit=10, offset=20
        )
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_session_success(self, mock_get_service, mock_get_user, client, mock_current_user, sample_session):
        """Test getting a specific session"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.get_session = AsyncMock(return_value=sample_session)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            f"/api/chat/sessions/{sample_session.id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_session.id
        assert data["title"] == "Test Session"
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_session_not_found(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting non-existent session"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.get_session = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions/non-existent-id",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_update_session_success(self, mock_get_service, mock_get_user, client, mock_current_user, sample_session):
        """Test updating a session"""
        mock_get_user.return_value = mock_current_user
        
        updated_session = ChatSession(
            id=sample_session.id,
            user_id=1,
            title="Updated Session Title",
            status="active"
        )
        
        mock_service = Mock()
        mock_service.update_session = AsyncMock(return_value=updated_session)
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            f"/api/chat/sessions/{sample_session.id}",
            json={"title": "Updated Session Title"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Session Title"
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_delete_session_success(self, mock_get_service, mock_get_user, client, mock_current_user, sample_session):
        """Test deleting a session"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.delete_session = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.delete(
            f"/api/chat/sessions/{sample_session.id}",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_delete_session_not_found(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test deleting non-existent session"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.delete_session = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        response = client.delete(
            "/api/chat/sessions/non-existent-id",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestChatMessageEndpoints:
    """Test cases for chat message endpoints"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_session_messages(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting messages for a session"""
        mock_get_user.return_value = mock_current_user
        
        messages = [
            ChatMessage(id="msg-1", session_id="session-1", role="user", content="Hello"),
            ChatMessage(id="msg-2", session_id="session-1", role="assistant", content="Hi there!")
        ]
        
        mock_service = Mock()
        mock_service.get_session_messages = AsyncMock(return_value=messages)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions/session-1/messages",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Hello"
        assert data[1]["content"] == "Hi there!"
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_send_message_streaming_success(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test sending a message with streaming response"""
        mock_get_user.return_value = mock_current_user
        
        # Mock streaming response
        async def mock_stream_response(session_id, user_id, message_data):
            yield StreamingResponse(type="chunk", content="Hello")
            yield StreamingResponse(type="chunk", content=" world!")
            yield StreamingResponse(type="complete", content="", message_id="msg-123")
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_response
        mock_get_service.return_value = mock_service
        
        message_data = {
            "content": "Hello, assistant!",
            "settings": {
                "model": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 2000
            },
            "context_options": {}
        }
        
        response = client.post(
            "/api/chat/sessions/session-1/messages",
            json=message_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse streaming response
        content = response.content.decode()
        lines = content.strip().split('\n')
        
        # Should contain data lines
        data_lines = [line for line in lines if line.startswith('data: ')]
        assert len(data_lines) >= 3  # At least 2 chunks + 1 complete
    
    def test_send_message_invalid_session_id(self, client):
        """Test sending message with invalid session ID format"""
        response = client.post(
            "/api/chat/sessions/invalid-uuid/messages",
            json={"content": "Hello"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should return 422 for invalid UUID format
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_send_message_empty_content(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test sending message with empty content"""
        mock_get_user.return_value = mock_current_user
        
        response = client.post(
            "/api/chat/sessions/test-session-id/messages",
            json={
                "content": "",
                "settings": {"model": "gpt-4"}
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestChatContextEndpoints:
    """Test cases for chat context endpoints"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_session_context(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting session context"""
        mock_get_user.return_value = mock_current_user
        
        context = ChatContext(
            session_id="session-1",
            problem_summary="Working on authentication",
            current_goal="Fix login issues",
            tasks=[{"description": "Review code", "status": "pending"}],
            relevant_documents=["doc1.md"]
        )
        
        mock_service = Mock()
        mock_service.get_session_context = AsyncMock(return_value=context)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions/session-1/context",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["problem_summary"] == "Working on authentication"
        assert data["current_goal"] == "Fix login issues"
        assert len(data["tasks"]) == 1
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_get_session_context_not_found(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test getting context for session without context"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.get_session_context = AsyncMock(return_value=None)
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/chat/sessions/session-1/context",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_update_session_context(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test updating session context"""
        mock_get_user.return_value = mock_current_user
        
        updated_context = ChatContext(
            session_id="session-1",
            problem_summary="Updated problem description",
            current_goal="New goal",
            tasks=[],
            relevant_documents=[]
        )
        
        mock_service = Mock()
        mock_service.update_session_context = AsyncMock(return_value=updated_context)
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/chat/sessions/session-1/context",
            json={
                "summary": "Updated problem description",
                "current_goal": "New goal"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["problem_summary"] == "Updated problem description"
        assert data["current_goal"] == "New goal"


class TestChatAPIAuthentication:
    """Test cases for authentication and authorization"""
    
    def test_endpoints_require_authentication(self, client):
        """Test that all endpoints require authentication"""
        endpoints = [
            ("GET", "/api/chat/sessions"),
            ("POST", "/api/chat/sessions"),
            ("GET", "/api/chat/sessions/test-id"),
            ("PATCH", "/api/chat/sessions/test-id"),
            ("DELETE", "/api/chat/sessions/test-id"),
            ("GET", "/api/chat/sessions/test-id/messages"),
            ("POST", "/api/chat/sessions/test-id/messages"),
            ("GET", "/api/chat/sessions/test-id/context"),
            ("PATCH", "/api/chat/sessions/test-id/context")
        ]
        
        for method, endpoint in endpoints:
            response = client.request(method, endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    @patch('app.api.chat.get_current_active_user')
    def test_inactive_user_access_denied(self, mock_get_user, client):
        """Test that inactive users are denied access"""
        inactive_user = Mock()
        inactive_user.id = 1
        inactive_user.is_active = False
        mock_get_user.return_value = inactive_user
        
        response = client.get(
            "/api/chat/sessions",
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should be handled by the authentication dependency
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]


class TestChatAPIErrorHandling:
    """Test cases for error handling in chat API"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_service_error_handling(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test handling of service layer errors"""
        mock_get_user.return_value = mock_current_user
        
        mock_service = Mock()
        mock_service.create_session = AsyncMock(side_effect=Exception("Database error"))
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/chat/sessions",
            json={"title": "Test Session"},
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_streaming_error_handling(self, mock_get_service, mock_get_user, client, mock_current_user):
        """Test error handling in streaming responses"""
        mock_get_user.return_value = mock_current_user
        
        async def mock_stream_with_error(session_id, user_id, message_data):
            yield StreamingResponse(type="chunk", content="Hello")
            yield StreamingResponse(type="error", content="", error="LLM service unavailable")
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_with_error
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/chat/sessions/session-1/messages",
            json={
                "content": "Hello",
                "settings": {"model": "gpt-4"}
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # Parse streaming response for error
        content = response.content.decode()
        assert "error" in content
        assert "LLM service unavailable" in content


class TestChatAPIValidation:
    """Test cases for request validation"""
    
    @patch('app.api.chat.get_current_active_user')
    def test_create_session_validation(self, mock_get_user, client, mock_current_user):
        """Test session creation request validation"""
        mock_get_user.return_value = mock_current_user
        
        # Test with invalid data types
        response = client.post(
            "/api/chat/sessions",
            json={"title": 123},  # Should be string
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @patch('app.api.chat.get_current_active_user')
    def test_send_message_validation(self, mock_get_user, client, mock_current_user):
        """Test message sending request validation"""
        mock_get_user.return_value = mock_current_user
        
        # Test missing required fields
        response = client.post(
            "/api/chat/sessions/test-session/messages",
            json={},  # Missing content and settings
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
        # Test invalid settings
        response = client.post(
            "/api/chat/sessions/test-session/messages",
            json={
                "content": "Hello",
                "settings": {
                    "model": "gpt-4",
                    "temperature": 2.0  # Should be <= 1.0
                }
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_uuid_validation(self, client):
        """Test UUID format validation for session IDs"""
        invalid_uuids = [
            "not-a-uuid",
            "123",
            "12345678-1234-1234-1234-12345678901",  # Too long
            "12345678-1234-1234-1234-123456789012"  # Invalid format
        ]
        
        for invalid_uuid in invalid_uuids:
            response = client.get(
                f"/api/chat/sessions/{invalid_uuid}",
                headers={"Authorization": "Bearer test-token"}
            )
            
            assert response.status_code in [
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_400_BAD_REQUEST
            ]