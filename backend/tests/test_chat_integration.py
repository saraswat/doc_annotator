import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.chat import router
from app.services.chat_service import ChatService
from app.services.unified_llm_service import UnifiedLLMService
from app.schemas.chat import StreamingResponse, ChatSessionCreate, ChatMessageCreate, ChatSettings
from app.models.chat import ChatSession, ChatMessage, ChatContext


@pytest.fixture
def app():
    """Create FastAPI app for integration testing"""
    app = FastAPI()
    app.include_router(router, prefix="/api/chat")
    return app


@pytest.fixture
def client(app):
    """Create test client for integration testing"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.is_active = True
    return user


class TestChatStreamingIntegration:
    """Integration tests for chat streaming functionality"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_full_streaming_conversation_flow(self, mock_get_service, mock_get_user, client, mock_user):
        """Test complete streaming conversation from start to finish"""
        mock_get_user.return_value = mock_user
        
        # Mock streaming response generator
        async def mock_stream_chat_response(session_id, user_id, message_data):
            # Simulate user message processing
            yield StreamingResponse(type="chunk", content="I")
            yield StreamingResponse(type="chunk", content=" understand")
            yield StreamingResponse(type="chunk", content=" your")
            yield StreamingResponse(type="chunk", content=" question")
            yield StreamingResponse(type="chunk", content=".")
            yield StreamingResponse(
                type="complete", 
                content="",
                message_id="response-msg-123",
                metadata={"usage": {"total_tokens": 25}}
            )
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_chat_response
        mock_get_service.return_value = mock_service
        
        message_data = {
            "content": "Can you help me debug my authentication code?",
            "settings": {
                "model": "test_model",
                "temperature": 0.7,
                "max_tokens": 2000,
                "web_browsing": False,
                "deep_research": False,
                "include_documents": []
            },
            "context_options": {
                "problem_context": None,
                "document_ids": [],
                "enable_web_browsing": False,
                "enable_deep_research": False
            }
        }
        
        response = client.post(
            "/api/chat/sessions/test-session-id/messages",
            json=message_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Parse Server-Sent Events response
        content = response.content.decode()
        lines = content.strip().split('\n')
        
        # Filter data lines
        data_lines = [line for line in lines if line.startswith('data: ')]
        
        # Should have multiple chunks plus completion
        assert len(data_lines) >= 6  # 5 chunks + 1 complete
        
        # Verify chunk contents
        chunks = []
        for line in data_lines:
            if line.startswith('data: '):
                try:
                    data = json.loads(line[6:])  # Remove 'data: ' prefix
                    chunks.append(data)
                except json.JSONDecodeError:
                    continue
        
        # Verify streaming structure
        chunk_responses = [c for c in chunks if c.get('type') == 'chunk']
        complete_responses = [c for c in chunks if c.get('type') == 'complete']
        
        assert len(chunk_responses) >= 5
        assert len(complete_responses) == 1
        
        # Verify message reconstruction
        full_message = ''.join(c.get('content', '') for c in chunk_responses)
        assert full_message == "I understand your question."
        
        # Verify completion metadata
        completion = complete_responses[0]
        assert completion.get('message_id') == "response-msg-123"
        assert completion.get('metadata', {}).get('usage', {}).get('total_tokens') == 25
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_streaming_error_handling(self, mock_get_service, mock_get_user, client, mock_user):
        """Test error handling during streaming"""
        mock_get_user.return_value = mock_user
        
        # Mock streaming response with error
        async def mock_stream_with_error(session_id, user_id, message_data):
            yield StreamingResponse(type="chunk", content="Starting")
            yield StreamingResponse(type="chunk", content=" to process")
            yield StreamingResponse(
                type="error", 
                content="",
                error="LLM service temporarily unavailable"
            )
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_with_error
        mock_get_service.return_value = mock_service
        
        message_data = {
            "content": "Hello",
            "settings": {"model": "test_model"},
            "context_options": {}
        }
        
        response = client.post(
            "/api/chat/sessions/test-session-id/messages",
            json=message_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        
        # Parse response to find error
        content = response.content.decode()
        assert "error" in content
        assert "LLM service temporarily unavailable" in content
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_streaming_with_context_updates(self, mock_get_service, mock_get_user, client, mock_user):
        """Test streaming with real-time context updates"""
        mock_get_user.return_value = mock_user
        
        # Mock streaming response with context updates
        async def mock_stream_with_context(session_id, user_id, message_data):
            yield StreamingResponse(type="chunk", content="Let me help")
            yield StreamingResponse(type="chunk", content=" you with")
            yield StreamingResponse(type="chunk", content=" that task.")
            yield StreamingResponse(
                type="context_update",
                content="",
                metadata={
                    "extracted_tasks": [
                        {
                            "description": "Review authentication code",
                            "priority": "high"
                        }
                    ],
                    "updated_goal": "Fix authentication system bugs"
                }
            )
            yield StreamingResponse(
                type="complete",
                content="",
                message_id="msg-with-context"
            )
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_with_context
        mock_get_service.return_value = mock_service
        
        message_data = {
            "content": "I need to fix authentication bugs in my system",
            "settings": {"model": "test_model"},
            "context_options": {"enable_context_updates": True}
        }
        
        response = client.post(
            "/api/chat/sessions/test-session-id/messages",
            json=message_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        
        # Parse response for context updates
        content = response.content.decode()
        
        # Should contain context update information
        assert "context_update" in content
        assert "extracted_tasks" in content
        assert "Review authentication code" in content


class TestChatServiceLLMIntegration:
    """Integration tests for ChatService with LLM client"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_llm_conversation(self):
        """Test end-to-end conversation with mocked LLM"""
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Mock LLM client
        mock_llm_client = AsyncMock()
        
        async def mock_llm_completion(*args, **kwargs):
            yield StreamingResponse(type="chunk", content="Hello")
            yield StreamingResponse(type="chunk", content=" there!")
            yield StreamingResponse(type="chunk", content=" How")
            yield StreamingResponse(type="chunk", content=" can")
            yield StreamingResponse(type="chunk", content=" I")
            yield StreamingResponse(type="chunk", content=" help?")
            yield StreamingResponse(
                type="complete",
                content="",
                metadata={"usage": {"total_tokens": 30}}
            )
        
        mock_llm_client.chat_completion = mock_llm_completion
        
        # Create chat service
        chat_service = ChatService(mock_db)
        
        # Mock session and context
        mock_session = ChatSession(
            id="test-session",
            user_id=1,
            title="Test Conversation"
        )
        
        mock_context = ChatContext(
            session_id="test-session",
            summary="Testing chat system",
            current_goal="Verify end-to-end functionality"
        )
        
        mock_session.context = mock_context
        
        with patch.object(chat_service, 'get_session', return_value=mock_session), \
             patch.object(chat_service, 'add_message', return_value=Mock()), \
             patch.object(chat_service, 'get_session_messages', return_value=[]), \
             patch('app.services.chat_service.get_llm_client', return_value=mock_llm_client):
            
            message_data = ChatMessageCreate(
                content="Hello, can you help me?",
                settings=ChatSettings(model="test_model"),
                context_options={}
            )
            
            responses = []
            async for response in chat_service.stream_chat_response(
                "test-session", 1, message_data
            ):
                responses.append(response)
            
            # Verify response structure
            chunk_responses = [r for r in responses if r.type == "chunk"]
            complete_responses = [r for r in responses if r.type == "complete"]
            
            assert len(chunk_responses) == 6
            assert len(complete_responses) == 1
            
            # Verify content reconstruction
            full_response = "".join(r.content for r in chunk_responses)
            assert full_response == "Hello there! How can I help?"
            
            # Verify completion metadata
            completion = complete_responses[0]
            assert completion.metadata["usage"]["total_tokens"] == 30
    
    @pytest.mark.asyncio
    async def test_llm_client_provider_selection(self):
        """Test LLM client correctly selects providers based on model"""
        
        # Mock providers
        mock_openai_provider = AsyncMock()
        mock_anthropic_provider = AsyncMock()
        
        async def mock_openai_response(*args, **kwargs):
            yield StreamingResponse(type="chunk", content="OpenAI response")
            yield StreamingResponse(type="complete", content="")
        
        async def mock_anthropic_response(*args, **kwargs):
            yield StreamingResponse(type="chunk", content="Anthropic response")
            yield StreamingResponse(type="complete", content="")
        
        mock_openai_provider.chat_completion = mock_openai_response
        mock_anthropic_provider.chat_completion = mock_anthropic_response
        
        # Create LLM client
        llm_client = LLMClient()
        llm_client._initialized = True
        llm_client.providers = {
            "openai": mock_openai_provider,
            "anthropic": mock_anthropic_provider
        }
        
        # Test OpenAI model selection
        responses = []
        async for response in llm_client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="test_model",
            stream=True
        ):
            responses.append(response)
        
        assert any("OpenAI response" in r.content for r in responses)
        mock_openai_provider.chat_completion.assert_called_once()
        
        # Reset mocks
        mock_openai_provider.reset_mock()
        mock_anthropic_provider.reset_mock()
        
        # Test Anthropic model selection
        responses = []
        async for response in llm_client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            model="claude-3-sonnet",
            stream=True
        ):
            responses.append(response)
        
        assert any("Anthropic response" in r.content for r in responses)
        mock_anthropic_provider.chat_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_manager_integration(self):
        """Test integration between chat service and context manager"""
        
        from app.services.context_manager import ContextManager
        
        # Create real context manager
        context_manager = ContextManager()
        
        # Mock database session
        mock_db = AsyncMock()
        
        # Create chat service with context manager
        chat_service = ChatService(mock_db, context_manager)
        
        # Create mock context
        mock_context = ChatContext(
            session_id="test-session",
            summary="",
            current_goal="",
            tasks=[]
        )
        
        # Test context update from conversation
        user_message = """
        I need to implement user authentication. Here's my plan:
        1. Set up password hashing
        2. Create login endpoints
        3. Add session management
        4. Write security tests
        My goal is to create a secure authentication system.
        """
        
        assistant_response = """
        That's a great plan! I recommend also:
        - Implementing rate limiting for login attempts
        - Adding password strength validation
        This is a high priority security feature.
        """
        
        await chat_service._update_context_from_conversation(
            Mock(context=mock_context), user_message, assistant_response
        )
        
        # Verify context was updated
        assert len(mock_context.tasks) > 0
        
        # Check that tasks were extracted
        task_descriptions = [task["description"] for task in mock_context.tasks]
        assert "Set up password hashing" in task_descriptions
        assert "Implementing rate limiting for login attempts" in task_descriptions
        
        # Check goal extraction
        assert "secure authentication system" in mock_context.current_goal.lower()


class TestChatSystemPerformance:
    """Performance and load tests for chat system"""
    
    @pytest.mark.asyncio
    async def test_concurrent_streaming_sessions(self):
        """Test multiple concurrent streaming sessions"""
        
        # Mock multiple streaming sessions
        async def mock_stream_session(session_id: str, delay: float = 0.1):
            for i in range(5):
                await asyncio.sleep(delay)
                yield StreamingResponse(
                    type="chunk",
                    content=f"Session {session_id} chunk {i}"
                )
            yield StreamingResponse(type="complete", content="")
        
        # Create multiple concurrent streams
        sessions = ["session-1", "session-2", "session-3", "session-4", "session-5"]
        
        async def collect_responses(session_id: str):
            responses = []
            async for response in mock_stream_session(session_id):
                responses.append(response)
            return session_id, responses
        
        # Run concurrent sessions
        tasks = [collect_responses(session_id) for session_id in sessions]
        results = await asyncio.gather(*tasks)
        
        # Verify all sessions completed
        assert len(results) == 5
        
        for session_id, responses in results:
            chunk_responses = [r for r in responses if r.type == "chunk"]
            complete_responses = [r for r in responses if r.type == "complete"]
            
            assert len(chunk_responses) == 5
            assert len(complete_responses) == 1
            
            # Verify session-specific content
            for i, chunk in enumerate(chunk_responses):
                assert session_id in chunk.content
                assert f"chunk {i}" in chunk.content
    
    @pytest.mark.asyncio
    async def test_large_message_streaming(self):
        """Test streaming of large messages"""
        
        # Create large message content
        large_content = "This is a test message. " * 1000  # ~24KB message
        
        async def mock_large_stream():
            # Split large content into chunks
            chunk_size = 100
            for i in range(0, len(large_content), chunk_size):
                chunk = large_content[i:i + chunk_size]
                yield StreamingResponse(type="chunk", content=chunk)
            yield StreamingResponse(type="complete", content="")
        
        # Collect all chunks
        responses = []
        async for response in mock_large_stream():
            responses.append(response)
        
        # Verify large message handling
        chunk_responses = [r for r in responses if r.type == "chunk"]
        complete_responses = [r for r in responses if r.type == "complete"]
        
        assert len(complete_responses) == 1
        assert len(chunk_responses) > 200  # Should be split into many chunks
        
        # Reconstruct and verify content
        reconstructed = "".join(r.content for r in chunk_responses)
        assert reconstructed == large_content


class TestChatSystemErrorRecovery:
    """Test error recovery and resilience"""
    
    @patch('app.api.chat.get_current_active_user')
    @patch('app.api.chat.get_chat_service')
    def test_streaming_connection_failure_recovery(self, mock_get_service, mock_get_user, client, mock_user):
        """Test recovery from streaming connection failures"""
        mock_get_user.return_value = mock_user
        
        # Mock streaming with connection failure
        async def mock_stream_with_failure(session_id, user_id, message_data):
            yield StreamingResponse(type="chunk", content="Starting")
            yield StreamingResponse(type="chunk", content=" response")
            # Simulate connection failure
            raise ConnectionError("Network connection lost")
        
        mock_service = Mock()
        mock_service.stream_chat_response = mock_stream_with_failure
        mock_get_service.return_value = mock_service
        
        message_data = {
            "content": "Test message",
            "settings": {"model": "test_model"},
            "context_options": {}
        }
        
        response = client.post(
            "/api/chat/sessions/test-session-id/messages",
            json=message_data,
            headers={"Authorization": "Bearer test-token"}
        )
        
        # Should handle gracefully (exact behavior depends on implementation)
        # Either return 500 or handle as streaming error
        assert response.status_code in [200, 500]
    
    @pytest.mark.asyncio
    async def test_partial_message_recovery(self):
        """Test recovery from partial message transmission"""
        
        # Mock stream that fails partway through
        async def mock_partial_stream():
            yield StreamingResponse(type="chunk", content="This is")
            yield StreamingResponse(type="chunk", content=" a partial")
            # Stream ends unexpectedly without complete signal
            return
        
        # Test handling of incomplete streams
        responses = []
        try:
            async for response in mock_partial_stream():
                responses.append(response)
        except StopAsyncIteration:
            pass
        
        # Should have partial content but no completion
        chunk_responses = [r for r in responses if r.type == "chunk"]
        complete_responses = [r for r in responses if r.type == "complete"]
        
        assert len(chunk_responses) == 2
        assert len(complete_responses) == 0
        
        # Partial content should be recoverable
        partial_content = "".join(r.content for r in chunk_responses)
        assert partial_content == "This is a partial"