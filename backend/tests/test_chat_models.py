import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.core.database import Base
from app.models.chat import ChatSession, ChatMessage, ChatContext
from app.models.user import User


@pytest.fixture
async def async_engine():
    """Create async SQLite engine for testing"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def async_session(async_engine):
    """Create async session for testing"""
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest.fixture
async def test_user(async_session):
    """Create test user for chat testing"""
    user = User(
        email="test@example.com",
        name="Test User",
        hashed_password="fake_hash",
        is_active=True,
        is_admin=False
    )
    
    async_session.add(user)
    await async_session.commit()
    await async_session.refresh(user)
    
    return user


class TestChatSession:
    """Test cases for ChatSession model"""
    
    @pytest.mark.asyncio
    async def test_create_chat_session(self, async_session, test_user):
        """Test creating a new chat session"""
        session = ChatSession(
            user_id=test_user.id,
            title="Test Session",
            status="active",
            session_metadata={"test": "data"},
            settings={"model": "test_model"}
        )
        
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        assert session.id is not None
        assert session.user_id == test_user.id
        assert session.title == "Test Session"
        assert session.status == "active"
        assert session.session_metadata == {"test": "data"}
        assert session.settings == {"model": "test_model"}
        assert session.message_count == 0
        assert session.total_tokens == 0
        assert session.created_at is not None
        assert session.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_chat_session_defaults(self, async_session, test_user):
        """Test default values for ChatSession"""
        session = ChatSession(user_id=test_user.id)
        
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        assert session.title == "New Chat"
        assert session.status == "active"
        assert session.session_metadata == {}
        assert session.settings == {}
        assert session.message_count == 0
        assert session.total_tokens == 0
    
    @pytest.mark.asyncio
    async def test_chat_session_user_relationship(self, async_session, test_user):
        """Test relationship between ChatSession and User"""
        session = ChatSession(
            user_id=test_user.id,
            title="Test Session"
        )
        
        async_session.add(session)
        await async_session.commit()
        
        # Test loading with relationship
        result = await async_session.execute(
            select(ChatSession).where(ChatSession.id == session.id)
        )
        loaded_session = result.scalar_one()
        
        # Test accessing user relationship
        await async_session.refresh(loaded_session, ['user'])
        assert loaded_session.user.id == test_user.id
        assert loaded_session.user.email == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_chat_session_cascade_delete(self, async_session, test_user):
        """Test cascade delete for chat session and related messages"""
        session = ChatSession(
            user_id=test_user.id,
            title="Test Session"
        )
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Add messages to the session
        message1 = ChatMessage(
            session_id=session.id,
            role="user",
            content="Hello"
        )
        message2 = ChatMessage(
            session_id=session.id,
            role="assistant",
            content="Hi there!"
        )
        
        async_session.add_all([message1, message2])
        await async_session.commit()
        
        # Verify messages exist
        result = await async_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 2
        
        # Delete the session
        await async_session.delete(session)
        await async_session.commit()
        
        # Verify messages were cascade deleted
        result = await async_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        messages = result.scalars().all()
        assert len(messages) == 0


class TestChatMessage:
    """Test cases for ChatMessage model"""
    
    @pytest.mark.asyncio
    async def test_create_chat_message(self, async_session, test_user):
        """Test creating a new chat message"""
        # Create session first
        session = ChatSession(user_id=test_user.id, title="Test Session")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create message
        message = ChatMessage(
            session_id=session.id,
            role="user",
            content="Hello, how are you?",
            tokens=15,
            model="test_model",
            message_metadata={"source": "web"},
            document_references=[{"doc_id": "doc1", "title": "Document 1"}],
            annotation_references=["annotation1", "annotation2"]
        )
        
        async_session.add(message)
        await async_session.commit()
        await async_session.refresh(message)
        
        assert message.id is not None
        assert message.session_id == session.id
        assert message.role == "user"
        assert message.content == "Hello, how are you?"
        assert message.tokens == 15
        assert message.model == "gpt-4"
        assert message.message_metadata == {"source": "web"}
        assert message.document_references == [{"doc_id": "doc1", "title": "Document 1"}]
        assert message.annotation_references == ["annotation1", "annotation2"]
        assert message.timestamp is not None
    
    @pytest.mark.asyncio
    async def test_chat_message_defaults(self, async_session, test_user):
        """Test default values for ChatMessage"""
        # Create session first
        session = ChatSession(user_id=test_user.id)
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create minimal message
        message = ChatMessage(
            session_id=session.id,
            role="user",
            content="Test message"
        )
        
        async_session.add(message)
        await async_session.commit()
        await async_session.refresh(message)
        
        assert message.tokens is None
        assert message.model is None
        assert message.message_metadata == {}
        assert message.document_references == []
        assert message.annotation_references == []
    
    @pytest.mark.asyncio
    async def test_chat_message_session_relationship(self, async_session, test_user):
        """Test relationship between ChatMessage and ChatSession"""
        # Create session
        session = ChatSession(user_id=test_user.id, title="Test Session")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create message
        message = ChatMessage(
            session_id=session.id,
            role="user",
            content="Test message"
        )
        async_session.add(message)
        await async_session.commit()
        
        # Test loading with relationship
        result = await async_session.execute(
            select(ChatMessage).where(ChatMessage.id == message.id)
        )
        loaded_message = result.scalar_one()
        
        # Test accessing session relationship
        await async_session.refresh(loaded_message, ['session'])
        assert loaded_message.session.id == session.id
        assert loaded_message.session.title == "Test Session"
    
    @pytest.mark.asyncio
    async def test_multiple_messages_same_session(self, async_session, test_user):
        """Test multiple messages in the same session"""
        # Create session
        session = ChatSession(user_id=test_user.id, title="Conversation")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create conversation
        messages = [
            ChatMessage(session_id=session.id, role="user", content="Hello"),
            ChatMessage(session_id=session.id, role="assistant", content="Hi there!"),
            ChatMessage(session_id=session.id, role="user", content="How are you?"),
            ChatMessage(session_id=session.id, role="assistant", content="I'm doing well, thank you!")
        ]
        
        async_session.add_all(messages)
        await async_session.commit()
        
        # Verify all messages are saved
        result = await async_session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.timestamp)
        )
        saved_messages = result.scalars().all()
        
        assert len(saved_messages) == 4
        assert saved_messages[0].content == "Hello"
        assert saved_messages[1].content == "Hi there!"
        assert saved_messages[2].content == "How are you?"
        assert saved_messages[3].content == "I'm doing well, thank you!"
        
        # Test conversation flow
        for i in range(len(saved_messages) - 1):
            assert saved_messages[i].timestamp <= saved_messages[i + 1].timestamp


class TestChatContext:
    """Test cases for ChatContext model"""
    
    @pytest.mark.asyncio
    async def test_create_chat_context(self, async_session, test_user):
        """Test creating a new chat context"""
        # Create session first
        session = ChatSession(user_id=test_user.id, title="Test Session")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create context
        context = ChatContext(
            session_id=session.id,
            summary="Working on user authentication system",
            current_goal="Fix login validation bug",
            tasks=[
                {
                    "id": "task-1",
                    "description": "Review authentication code",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "id": "task-2",
                    "description": "Write unit tests",
                    "status": "completed",
                    "priority": "medium"
                }
            ],
            relevant_documents=["auth_spec.md", "api_docs.json"],
            context_metadata={"complexity": "medium", "estimated_hours": 8}
        )
        
        async_session.add(context)
        await async_session.commit()
        await async_session.refresh(context)
        
        assert context.id is not None
        assert context.session_id == session.id
        assert context.summary == "Working on user authentication system"
        assert context.current_goal == "Fix login validation bug"
        assert len(context.tasks) == 2
        assert context.tasks[0]["description"] == "Review authentication code"
        assert context.tasks[1]["status"] == "completed"
        assert context.relevant_documents == ["auth_spec.md", "api_docs.json"]
        assert context.context_metadata == {"complexity": "medium", "estimated_hours": 8}
        assert context.created_at is not None
        assert context.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_chat_context_defaults(self, async_session, test_user):
        """Test default values for ChatContext"""
        # Create session first
        session = ChatSession(user_id=test_user.id)
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create minimal context
        context = ChatContext(session_id=session.id)
        
        async_session.add(context)
        await async_session.commit()
        await async_session.refresh(context)
        
        assert context.summary is None
        assert context.current_goal is None
        assert context.tasks == []
        assert context.relevant_documents == []
        assert context.context_metadata == {}
    
    @pytest.mark.asyncio
    async def test_chat_context_session_relationship(self, async_session, test_user):
        """Test one-to-one relationship between ChatContext and ChatSession"""
        # Create session
        session = ChatSession(user_id=test_user.id, title="Test Session")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create context
        context = ChatContext(
            session_id=session.id,
            summary="Test problem"
        )
        async_session.add(context)
        await async_session.commit()
        
        # Test loading with relationship
        result = await async_session.execute(
            select(ChatContext).where(ChatContext.session_id == session.id)
        )
        loaded_context = result.scalar_one()
        
        # Test accessing session relationship
        await async_session.refresh(loaded_context, ['session'])
        assert loaded_context.session.id == session.id
        assert loaded_context.session.title == "Test Session"
        
        # Test reverse relationship
        result = await async_session.execute(
            select(ChatSession).where(ChatSession.id == session.id)
        )
        loaded_session = result.scalar_one()
        
        await async_session.refresh(loaded_session, ['context'])
        assert loaded_session.context.summary == "Test problem"
    
    @pytest.mark.asyncio
    async def test_chat_context_unique_constraint(self, async_session, test_user):
        """Test that only one context can exist per session"""
        # Create session
        session = ChatSession(user_id=test_user.id)
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Create first context
        context1 = ChatContext(
            session_id=session.id,
            summary="First context"
        )
        async_session.add(context1)
        await async_session.commit()
        
        # Try to create second context for same session
        context2 = ChatContext(
            session_id=session.id,
            summary="Second context"
        )
        async_session.add(context2)
        
        # Should raise integrity error
        with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
            await async_session.commit()
    
    @pytest.mark.asyncio
    async def test_chat_context_json_fields_modification(self, async_session, test_user):
        """Test modifying JSON fields in ChatContext"""
        # Create session and context
        session = ChatSession(user_id=test_user.id)
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        context = ChatContext(
            session_id=session.id,
            tasks=[],
            relevant_documents=[]
        )
        async_session.add(context)
        await async_session.commit()
        await async_session.refresh(context)
        
        # Modify tasks
        context.tasks = [
            {"id": "task-1", "description": "New task", "status": "pending"}
        ]
        context.relevant_documents = ["new_doc.md"]
        
        await async_session.commit()
        
        # Reload and verify changes
        result = await async_session.execute(
            select(ChatContext).where(ChatContext.id == context.id)
        )
        updated_context = result.scalar_one()
        
        assert len(updated_context.tasks) == 1
        assert updated_context.tasks[0]["description"] == "New task"
        assert updated_context.relevant_documents == ["new_doc.md"]


class TestChatModelsIntegration:
    """Integration tests for all chat models working together"""
    
    @pytest.mark.asyncio
    async def test_full_chat_workflow(self, async_session, test_user):
        """Test complete workflow: session -> messages -> context"""
        # Create chat session
        session = ChatSession(
            user_id=test_user.id,
            title="Problem Solving Session",
            settings={"model": "test_model", "temperature": 0.7}
        )
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        # Add messages to the conversation
        messages = [
            ChatMessage(
                session_id=session.id,
                role="user",
                content="I need help fixing a bug in my authentication system"
            ),
            ChatMessage(
                session_id=session.id,
                role="assistant",
                content="I'd be happy to help! Can you describe the specific issue you're experiencing?"
            ),
            ChatMessage(
                session_id=session.id,
                role="user",
                content="Users are getting 'Invalid credentials' even with correct passwords"
            ),
            ChatMessage(
                session_id=session.id,
                role="assistant", 
                content="Let's debug this step by step. First, let's check the password hashing logic.",
                model="test_model",
                tokens=45
            )
        ]
        
        async_session.add_all(messages)
        await async_session.commit()
        
        # Create context based on the conversation
        context = ChatContext(
            session_id=session.id,
            summary="User authentication system bug - invalid credentials error",
            current_goal="Debug and fix password validation issue",
            tasks=[
                {
                    "id": "task-1",
                    "description": "Check password hashing logic",
                    "status": "pending",
                    "priority": "high"
                },
                {
                    "id": "task-2",
                    "description": "Verify database user records",
                    "status": "pending",
                    "priority": "medium"
                },
                {
                    "id": "task-3",
                    "description": "Test login flow end-to-end",
                    "status": "pending",
                    "priority": "high"
                }
            ],
            relevant_documents=["auth_system.py", "user_model.py"]
        )
        async_session.add(context)
        await async_session.commit()
        
        # Update session stats
        session.message_count = len(messages)
        session.total_tokens = sum(msg.tokens or 0 for msg in messages)
        session.last_message = "Let's debug this step by step..."
        
        await async_session.commit()
        
        # Verify complete workflow
        result = await async_session.execute(
            select(ChatSession)
            .where(ChatSession.id == session.id)
        )
        final_session = result.scalar_one()
        
        # Load all relationships
        await async_session.refresh(final_session, ['messages', 'context'])
        
        # Verify session
        assert final_session.title == "Problem Solving Session"
        assert final_session.message_count == 4
        assert final_session.total_tokens == 45
        assert "debug this step by step" in final_session.last_message
        
        # Verify messages
        assert len(final_session.messages) == 4
        assert final_session.messages[0].role == "user"
        assert "authentication system" in final_session.messages[0].content
        assert final_session.messages[-1].model == "gpt-4"
        
        # Verify context
        assert final_session.context is not None
        assert "authentication system bug" in final_session.context.summary
        assert len(final_session.context.tasks) == 3
        assert "Check password hashing logic" in str(final_session.context.tasks)
        assert "auth_system.py" in final_session.context.relevant_documents
    
    @pytest.mark.asyncio
    async def test_cascade_delete_complete_workflow(self, async_session, test_user):
        """Test that deleting a user cascades to all chat data"""
        # Create complete chat structure
        session = ChatSession(user_id=test_user.id, title="Test Session")
        async_session.add(session)
        await async_session.commit()
        await async_session.refresh(session)
        
        message = ChatMessage(
            session_id=session.id,
            role="user", 
            content="Test message"
        )
        async_session.add(message)
        
        context = ChatContext(
            session_id=session.id,
            summary="Test context"
        )
        async_session.add(context)
        
        await async_session.commit()
        
        # Verify everything exists
        sessions_result = await async_session.execute(
            select(ChatSession).where(ChatSession.user_id == test_user.id)
        )
        assert len(sessions_result.scalars().all()) == 1
        
        messages_result = await async_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        assert len(messages_result.scalars().all()) == 1
        
        context_result = await async_session.execute(
            select(ChatContext).where(ChatContext.session_id == session.id)
        )
        assert len(context_result.scalars().all()) == 1
        
        # Delete the user
        await async_session.delete(test_user)
        await async_session.commit()
        
        # Verify cascade deletion worked
        sessions_result = await async_session.execute(
            select(ChatSession).where(ChatSession.user_id == test_user.id)
        )
        assert len(sessions_result.scalars().all()) == 0
        
        messages_result = await async_session.execute(
            select(ChatMessage).where(ChatMessage.session_id == session.id)
        )
        assert len(messages_result.scalars().all()) == 0
        
        context_result = await async_session.execute(
            select(ChatContext).where(ChatContext.session_id == session.id)
        )
        assert len(context_result.scalars().all()) == 0