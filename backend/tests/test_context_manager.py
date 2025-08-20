import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from app.services.context_manager import ContextManager
from app.models.chat import ChatContext


@pytest.fixture
def context_manager():
    """Context manager instance for testing"""
    return ContextManager()


@pytest.fixture
def sample_context():
    """Sample chat context for testing"""
    return ChatContext(
        session_id="test-session-id",
        summary="Working on user authentication system",
        current_goal="Fix login validation bug",
        tasks=[
            {
                "id": "task-1",
                "description": "Review authentication code",
                "status": "completed",
                "priority": "high",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "task-2", 
                "description": "Test login functionality",
                "status": "pending",
                "priority": "medium",
                "created_at": datetime.utcnow().isoformat()
            }
        ],
        relevant_documents=["auth_doc.md", "api_spec.json"]
    )


class TestContextManager:
    """Test cases for ContextManager"""
    
    @pytest.mark.asyncio
    async def test_extract_tasks_from_numbered_list(self, context_manager):
        """Test extracting tasks from numbered list"""
        text = """
        Here's what we need to do:
        1. Review the login code
        2. Fix the validation bug
        3. Test the authentication system
        4. Update the documentation
        """
        
        tasks = context_manager._extract_tasks(text)
        
        assert len(tasks) >= 4
        task_descriptions = [task["description"] for task in tasks]
        assert "Review the login code" in task_descriptions
        assert "Fix the validation bug" in task_descriptions
        assert "Test the authentication system" in task_descriptions
        assert "Update the documentation" in task_descriptions
    
    @pytest.mark.asyncio
    async def test_extract_tasks_from_bullet_points(self, context_manager):
        """Test extracting tasks from bullet points"""
        text = """
        Our action items:
        - Check the database connection
        - Validate user input parameters
        - Implement error handling
        * Review security measures
        """
        
        tasks = context_manager._extract_tasks(text)
        
        assert len(tasks) >= 3
        task_descriptions = [task["description"] for task in tasks]
        assert "Check the database connection" in task_descriptions
        assert "Validate user input parameters" in task_descriptions
        assert "Implement error handling" in task_descriptions
    
    @pytest.mark.asyncio
    async def test_extract_tasks_from_todo_markers(self, context_manager):
        """Test extracting tasks from TODO markers"""
        text = """
        TODO: Refactor the authentication module
        Task: Write unit tests for login
        Action: Deploy to staging environment
        """
        
        tasks = context_manager._extract_tasks(text)
        
        assert len(tasks) >= 3
        task_descriptions = [task["description"] for task in tasks]
        assert "Refactor the authentication module" in task_descriptions
        assert "Write unit tests for login" in task_descriptions
        assert "Deploy to staging environment" in task_descriptions
    
    def test_extract_tasks_filters_short_text(self, context_manager):
        """Test that very short task descriptions are filtered out"""
        text = """
        1. Fix
        2. This is a proper task description
        3. Do
        """
        
        tasks = context_manager._extract_tasks(text)
        
        # Should only get the longer task
        assert len(tasks) == 1
        assert tasks[0]["description"] == "This is a proper task description"
    
    def test_extract_tasks_filters_questions(self, context_manager):
        """Test that questions are filtered out from tasks"""
        text = """
        - What should we do about the bug?
        - Fix the authentication issue
        - How can we improve performance?
        - Update the documentation
        """
        
        tasks = context_manager._extract_tasks(text)
        
        # Should only get non-question tasks
        task_descriptions = [task["description"] for task in tasks]
        assert "Fix the authentication issue" in task_descriptions
        assert "Update the documentation" in task_descriptions
        assert "What should we do about the bug?" not in task_descriptions
        assert "How can we improve performance?" not in task_descriptions
    
    def test_extract_goals_from_text(self, context_manager):
        """Test extracting goals from text"""
        text = """
        I'm trying to fix the login authentication system. The goal is to 
        resolve the validation errors that users are experiencing. We're 
        working on improving the security of our application.
        """
        
        goals = context_manager._extract_goals(text)
        
        assert len(goals) >= 1
        assert "fix the login authentication system" in goals[0].lower()
    
    def test_determine_priority_high(self, context_manager):
        """Test determining high priority from keywords"""
        high_priority_texts = [
            "Urgent: Fix the critical authentication bug",
            "This is a critical issue that needs immediate attention",
            "ASAP - resolve the login problem",
            "High priority task to complete"
        ]
        
        for text in high_priority_texts:
            priority = context_manager._determine_priority(text)
            assert priority == "high"
    
    def test_determine_priority_low(self, context_manager):
        """Test determining low priority from keywords"""
        low_priority_texts = [
            "Eventually we might want to refactor this",
            "Consider adding this feature later",
            "This is optional and nice to have",
            "Maybe we could improve this"
        ]
        
        for text in low_priority_texts:
            priority = context_manager._determine_priority(text)
            assert priority == "low"
    
    def test_determine_priority_medium_default(self, context_manager):
        """Test that medium priority is default"""
        text = "Complete the code review process"
        priority = context_manager._determine_priority(text)
        assert priority == "medium"
    
    def test_text_similarity(self, context_manager):
        """Test text similarity calculation"""
        text1 = "fix the authentication bug"
        text2 = "fix the authentication issue" 
        text3 = "update the documentation"
        
        # Similar texts
        similarity1 = context_manager._text_similarity(text1, text2)
        assert similarity1 > 0.5
        
        # Different texts
        similarity2 = context_manager._text_similarity(text1, text3)
        assert similarity2 < 0.5
        
        # Identical texts
        similarity3 = context_manager._text_similarity(text1, text1)
        assert similarity3 == 1.0
    
    def test_deduplicate_tasks(self, context_manager):
        """Test deduplicating similar tasks"""
        tasks = [
            {
                "description": "Fix the authentication bug",
                "priority": "high"
            },
            {
                "description": "Fix the authentication issue", 
                "priority": "medium"
            },
            {
                "description": "Update documentation",
                "priority": "low"
            }
        ]
        
        unique_tasks = context_manager._deduplicate_tasks(tasks)
        
        # Should remove the duplicate authentication task
        assert len(unique_tasks) == 2
        descriptions = [task["description"] for task in unique_tasks]
        assert "Update documentation" in descriptions
        # Should keep the first authentication task
        assert "Fix the authentication bug" in descriptions
    
    @pytest.mark.asyncio
    async def test_update_tasks(self, context_manager, sample_context):
        """Test updating context tasks with new extracted tasks"""
        new_tasks = [
            {
                "description": "Deploy to production environment",
                "priority": "high",
                "source": "extracted"
            },
            {
                "description": "Review authentication code",  # Duplicate
                "priority": "medium", 
                "source": "extracted"
            }
        ]
        
        original_task_count = len(sample_context.tasks)
        
        await context_manager._update_tasks(sample_context, new_tasks)
        
        # Should add only the non-duplicate task
        assert len(sample_context.tasks) == original_task_count + 1
        
        # Check that the new unique task was added
        task_descriptions = [task["description"] for task in sample_context.tasks]
        assert "Deploy to production environment" in task_descriptions
    
    @pytest.mark.asyncio
    async def test_update_goals(self, context_manager, sample_context):
        """Test updating context goals"""
        new_goals = [
            "Improve system performance",
            "This is a longer and more specific goal about enhancing user experience"
        ]
        
        await context_manager._update_goals(sample_context, new_goals)
        
        # Should use the longer, more specific goal
        assert sample_context.current_goal == "This is a longer and more specific goal about enhancing user experience"
    
    @pytest.mark.asyncio
    async def test_update_summary(self, context_manager):
        """Test updating problem summary"""
        context = ChatContext(session_id="test")
        user_message = "I'm having trouble with the login system. Users can't authenticate properly."
        assistant_response = "I can help you debug the authentication issue."
        
        await context_manager._update_summary(context, user_message, assistant_response)
        
        assert context.summary is not None
        assert len(context.summary) > 0
        assert "having trouble with the login system" in context.summary
    
    @pytest.mark.asyncio
    async def test_update_from_conversation(self, context_manager):
        """Test updating context from full conversation"""
        context = ChatContext(
            session_id="test-session",
            summary="",
            current_goal="",
            tasks=[]
        )
        
        user_message = """
        I need to fix the authentication system. Here's what I need to do:
        1. Review the login code
        2. Test the validation logic
        3. Update the error messages
        My goal is to resolve all authentication issues.
        """
        
        assistant_response = """
        I can help you with that. Here are some additional steps:
        - Check the database connection
        - Verify the password hashing
        This is a high priority issue that needs immediate attention.
        """
        
        await context_manager.update_from_conversation(context, user_message, assistant_response)
        
        # Check that tasks were extracted
        assert len(context.tasks) > 0
        task_descriptions = [task["description"] for task in context.tasks]
        assert "Review the login code" in task_descriptions
        assert "Check the database connection" in task_descriptions
        
        # Check that goal was extracted
        assert "resolve all authentication issues" in context.current_goal.lower()
        
        # Check that summary was created
        assert context.summary is not None
        assert len(context.summary) > 0
    
    @pytest.mark.asyncio
    async def test_extract_document_relevance(self, context_manager):
        """Test extracting relevant documents from conversation"""
        context = ChatContext(session_id="test")
        
        conversation_text = """
        I need help with the authentication system. Please review the auth_spec.md 
        document and check the api_documentation.json file. The user_guide.pdf 
        might also have relevant information about login flows.
        """
        
        available_documents = [
            {"id": "doc1", "title": "Authentication Specification", "tags": ["auth", "spec"]},
            {"id": "doc2", "title": "API Documentation", "tags": ["api", "docs"]}, 
            {"id": "doc3", "title": "User Guide", "tags": ["user", "guide"]},
            {"id": "doc4", "title": "Database Schema", "tags": ["database", "schema"]}
        ]
        
        relevant_docs = await context_manager.extract_document_relevance(
            context, conversation_text, available_documents
        )
        
        # Should identify auth and api docs as relevant
        assert "doc1" in relevant_docs  # Authentication Specification
        assert "doc2" in relevant_docs  # API Documentation
        assert "doc3" in relevant_docs  # User Guide
        # Database schema should not be relevant
        assert "doc4" not in relevant_docs
    
    @pytest.mark.asyncio
    async def test_generate_context_insights(self, context_manager, sample_context):
        """Test generating insights about context"""
        insights = await context_manager.generate_context_insights(sample_context)
        
        assert "task_summary" in insights
        assert insights["task_summary"]["total"] == 2
        assert insights["task_summary"]["completed"] == 1
        assert insights["task_summary"]["pending"] == 1
        assert insights["task_summary"]["high_priority"] == 1
        
        assert "progress_percentage" in insights
        assert insights["progress_percentage"] == 50.0  # 1 out of 2 tasks completed
        
        assert "next_suggested_action" in insights
        assert insights["next_suggested_action"] == "Test login functionality"
        
        assert "estimated_complexity" in insights
        assert insights["estimated_complexity"] == "simple"  # 2 tasks = simple
    
    @pytest.mark.asyncio
    async def test_generate_context_insights_complex(self, context_manager):
        """Test insights generation for complex context"""
        complex_context = ChatContext(
            session_id="test",
            tasks=[
                {"description": f"Task {i}", "status": "pending", "priority": "medium"}
                for i in range(8)  # 8 tasks = complex
            ]
        )
        
        insights = await context_manager.generate_context_insights(complex_context)
        
        assert insights["estimated_complexity"] == "complex"
        assert insights["progress_percentage"] == 0.0
        assert insights["task_summary"]["total"] == 8
    
    @pytest.mark.asyncio 
    async def test_update_from_conversation_error_handling(self, context_manager):
        """Test error handling in update_from_conversation"""
        context = ChatContext(session_id="test")
        
        # Test with invalid input that might cause errors
        user_message = None
        assistant_response = ""
        
        # Should not raise exception
        await context_manager.update_from_conversation(context, user_message, assistant_response)
        
        # Context should remain in valid state
        assert context.session_id == "test"


class TestContextManagerTaskExtraction:
    """Focused tests for task extraction functionality"""
    
    def test_extract_complex_tasks(self, context_manager):
        """Test extracting tasks from complex mixed format text"""
        text = """
        Project roadmap for Q1:
        
        Phase 1 - Authentication:
        1. Review current auth system
        2. Identify security vulnerabilities
        3. Implement two-factor authentication
        
        Phase 2 - Performance:
        - Optimize database queries
        - Implement caching layer
        - Load test the system
        
        Critical issues:
        TODO: Fix the password reset bug (urgent)
        Action: Update SSL certificates
        
        Nice to have:
        * Add social login options
        * Improve UI/UX design
        """
        
        tasks = context_manager._extract_tasks(text)
        
        # Should extract tasks from all formats
        assert len(tasks) >= 8
        
        task_descriptions = [task["description"] for task in tasks]
        
        # Check numbered list items
        assert "Review current auth system" in task_descriptions
        assert "Implement two-factor authentication" in task_descriptions
        
        # Check bullet points
        assert "Optimize database queries" in task_descriptions
        assert "Implement caching layer" in task_descriptions
        
        # Check TODO/Action items
        assert "Fix the password reset bug (urgent)" in task_descriptions
        assert "Update SSL certificates" in task_descriptions
        
        # Check priorities are assigned correctly
        urgent_tasks = [task for task in tasks if task["priority"] == "high"]
        assert any("urgent" in task["description"] for task in urgent_tasks)
    
    def test_extract_tasks_with_context_filtering(self, context_manager):
        """Test that task extraction filters out non-actionable items"""
        text = """
        Meeting notes:
        - John mentioned the database issue
        - What should we do about performance?
        - The system is running slowly
        - Fix the login bug immediately
        - Can we improve the UI?
        - Update the documentation
        - Where is the config file located?
        """
        
        tasks = context_manager._extract_tasks(text)
        
        task_descriptions = [task["description"] for task in tasks]
        
        # Should include actionable items
        assert "Fix the login bug immediately" in task_descriptions
        assert "Update the documentation" in task_descriptions
        
        # Should exclude questions and observations
        assert "What should we do about performance?" not in task_descriptions
        assert "Can we improve the UI?" not in task_descriptions
        assert "Where is the config file located?" not in task_descriptions
        assert "John mentioned the database issue" not in task_descriptions
        assert "The system is running slowly" not in task_descriptions


class TestContextManagerGoalExtraction:
    """Focused tests for goal extraction functionality"""
    
    def test_extract_various_goal_patterns(self, context_manager):
        """Test extracting goals from various sentence patterns"""
        texts_and_expected = [
            ("I'm trying to fix the authentication system", "fix the authentication system"),
            ("Our goal is to improve user experience", "improve user experience"),
            ("The objective is to reduce response time", "reduce response time"),
            ("We're working on enhancing security", "enhancing security"),
            ("I need to resolve the database connection issue", "resolve the database connection issue"),
            ("The aim is to streamline the workflow", "streamline the workflow")
        ]
        
        for text, expected in texts_and_expected:
            goals = context_manager._extract_goals(text)
            assert len(goals) >= 1
            assert expected in goals[0].lower()
    
    def test_extract_goals_filters_short_matches(self, context_manager):
        """Test that very short goal matches are filtered out"""
        text = "I'm trying to fix it and working on stuff"
        
        goals = context_manager._extract_goals(text)
        
        # Should not extract very short/generic goals
        assert len(goals) == 0 or all(len(goal) > 10 for goal in goals)