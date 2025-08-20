"""
Pytest configuration and shared fixtures for chat system tests
"""
import pytest
import asyncio
import os
import sys
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database_config import Base
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage, ChatContext


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_engine():
    """Create a test database engine using SQLite in memory."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create an async database session for testing."""
    async_session_factory = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_factory() as session:
        yield session


@pytest.fixture
async def test_user(async_session) -> User:
    """Create a test user for chat testing."""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="fake_hashed_password",
        is_active=True,
        is_admin=False
    )
    
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


@pytest.fixture
async def test_chat_session(async_session, test_user) -> ChatSession:
    """Create a test chat session."""
    session = ChatSession(
        user_id=test_user.id,
        title="Test Chat Session",
        status="active",
        session_metadata={"test": "data"},
        settings={"model": "gpt-4", "temperature": 0.7}
    )
    
    async_session.add(session)
    await async_session.commit()
    await async_session.refresh(session)
    
    return session


@pytest.fixture
async def test_chat_messages(async_session, test_chat_session) -> list[ChatMessage]:
    """Create test chat messages."""
    messages = [
        ChatMessage(
            session_id=test_chat_session.id,
            role="user",
            content="Hello, can you help me with my project?",
            message_metadata={"source": "test"}
        ),
        ChatMessage(
            session_id=test_chat_session.id,
            role="assistant",
            content="Of course! I'd be happy to help you with your project. What specific area would you like assistance with?",
            model="gpt-4",
            tokens=25,
            message_metadata={"completion_reason": "stop"}
        ),
        ChatMessage(
            session_id=test_chat_session.id,
            role="user",
            content="I'm working on a Python web application and need help with authentication.",
            message_metadata={"source": "test"}
        )
    ]
    
    async_session.add_all(messages)
    await async_session.commit()
    
    for message in messages:
        await async_session.refresh(message)
    
    return messages


@pytest.fixture
async def test_chat_context(async_session, test_chat_session) -> ChatContext:
    """Create test chat context."""
    context = ChatContext(
        session_id=test_chat_session.id,
        summary="User needs help with Python web application authentication",
        current_goal="Implement secure user authentication system",
        tasks=[
            {
                "id": "task-1",
                "description": "Set up password hashing",
                "status": "pending",
                "priority": "high",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "task-2",
                "description": "Implement login endpoints",
                "status": "pending",
                "priority": "high", 
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "task-3",
                "description": "Add session management",
                "status": "completed",
                "priority": "medium",
                "created_at": "2024-01-01T00:00:00Z",
                "completed_at": "2024-01-02T00:00:00Z"
            }
        ],
        relevant_documents=["auth_guide.md", "security_best_practices.md"],
        context_metadata={"complexity": "medium", "estimated_hours": 6}
    )
    
    async_session.add(context)
    await async_session.commit()
    await async_session.refresh(context)
    
    return context


@pytest.fixture
def mock_llm_responses():
    """Predefined LLM responses for testing."""
    return {
        "simple_response": [
            {"type": "chunk", "content": "Hello"},
            {"type": "chunk", "content": " there!"},
            {"type": "complete", "content": "", "metadata": {"usage": {"total_tokens": 10}}}
        ],
        "code_help_response": [
            {"type": "chunk", "content": "I can help you"},
            {"type": "chunk", "content": " with your authentication"},
            {"type": "chunk", "content": " system. Here's what"},
            {"type": "chunk", "content": " I recommend:"},
            {"type": "complete", "content": "", "metadata": {"usage": {"total_tokens": 45}}}
        ],
        "error_response": [
            {"type": "chunk", "content": "I'm sorry"},
            {"type": "error", "error": "Service temporarily unavailable"}
        ]
    }


# Mark async tests
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location and name."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Mark tests with long-running operations
        if any(keyword in item.name for keyword in ["concurrent", "large", "performance"]):
            item.add_marker(pytest.mark.slow)