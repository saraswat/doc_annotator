import re
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models.chat import ChatContext

logger = logging.getLogger(__name__)

class ContextManager:
    """Service for managing problem context and task extraction"""
    
    def __init__(self):
        self.task_patterns = [
            r"(?i)(?:need to|should|must|have to|going to|will)\s+([^.]+)",
            r"(?i)(?:todo|to-do|task):\s*([^.]+)",
            r"(?i)(?:action|step)\s*\d*:\s*([^.]+)",
            r"(?i)(?:next|then|after that),?\s*([^.]+)",
        ]
        
        self.goal_patterns = [
            r"(?i)(?:trying to|wanting to|need to|goal is to|objective is to|aim is to)\s+([^.]+)",
            r"(?i)(?:working on|focusing on)\s+([^.]+)",
            r"(?i)(?:problem|issue|challenge):\s*([^.]+)",
        ]
        
        self.priority_keywords = {
            "high": ["urgent", "critical", "important", "asap", "priority", "immediately"],
            "medium": ["should", "need", "important", "soon"],
            "low": ["might", "could", "eventually", "later", "someday"]
        }
    
    async def update_from_conversation(
        self,
        context: ChatContext,
        user_message: str,
        assistant_response: str
    ) -> None:
        """Update context based on conversation content"""
        try:
            # Extract new tasks from both messages
            user_tasks = self._extract_tasks(user_message)
            assistant_tasks = self._extract_tasks(assistant_response)
            
            # Extract potential goals/problems
            user_goals = self._extract_goals(user_message)
            assistant_goals = self._extract_goals(assistant_response)
            
            # Update context
            await self._update_tasks(context, user_tasks + assistant_tasks)
            await self._update_goals(context, user_goals + assistant_goals)
            await self._update_summary(context, user_message, assistant_response)
            
        except Exception as e:
            logger.error(f"Error updating context from conversation: {str(e)}")
    
    def _extract_tasks(self, text: str) -> List[Dict[str, Any]]:
        """Extract actionable tasks from text"""
        tasks = []
        
        for pattern in self.task_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                task_text = match.strip()
                if len(task_text) > 5:  # Filter out very short matches
                    tasks.append({
                        "description": task_text,
                        "priority": self._determine_priority(task_text),
                        "source": "extracted",
                        "created_at": datetime.utcnow().isoformat()
                    })
        
        # Look for numbered lists
        numbered_tasks = re.findall(r"(?i)^\s*\d+\.\s*([^.]+)", text, re.MULTILINE)
        for task in numbered_tasks:
            task_text = task.strip()
            if len(task_text) > 5:
                tasks.append({
                    "description": task_text,
                    "priority": self._determine_priority(task_text),
                    "source": "numbered_list",
                    "created_at": datetime.utcnow().isoformat()
                })
        
        # Look for bullet points
        bullet_tasks = re.findall(r"(?i)^\s*[-*]\s*([^.]+)", text, re.MULTILINE)
        for task in bullet_tasks:
            task_text = task.strip()
            if len(task_text) > 5 and not self._is_question(task_text):
                tasks.append({
                    "description": task_text,
                    "priority": self._determine_priority(task_text),
                    "source": "bullet_list",
                    "created_at": datetime.utcnow().isoformat()
                })
        
        return self._deduplicate_tasks(tasks)
    
    def _extract_goals(self, text: str) -> List[str]:
        """Extract goals and objectives from text"""
        goals = []
        
        for pattern in self.goal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                goal_text = match.strip()
                if len(goal_text) > 10:  # Filter out very short matches
                    goals.append(goal_text)
        
        return goals
    
    def _determine_priority(self, text: str) -> str:
        """Determine task priority based on keywords"""
        text_lower = text.lower()
        
        for priority, keywords in self.priority_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return priority
        
        return "medium"  # Default priority
    
    def _is_question(self, text: str) -> bool:
        """Check if text is a question"""
        question_words = ["what", "how", "why", "when", "where", "who", "which", "can", "could", "would", "should"]
        text_lower = text.lower().strip()
        
        return (
            text.endswith("?") or
            any(text_lower.startswith(word) for word in question_words)
        )
    
    def _deduplicate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tasks based on similarity"""
        unique_tasks = []
        seen_descriptions = set()
        
        for task in tasks:
            description = task["description"].lower().strip()
            
            # Simple similarity check - if 80% of words match, consider duplicate
            is_duplicate = False
            for seen in seen_descriptions:
                if self._text_similarity(description, seen) > 0.8:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_tasks.append(task)
                seen_descriptions.add(description)
        
        return unique_tasks
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity based on common words"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    async def _update_tasks(self, context: ChatContext, new_tasks: List[Dict[str, Any]]) -> None:
        """Update context tasks with new extracted tasks"""
        if not new_tasks:
            return
        
        existing_tasks = context.tasks or []
        
        # Add new tasks that aren't already present
        for new_task in new_tasks:
            is_duplicate = False
            
            for existing_task in existing_tasks:
                existing_desc = existing_task.get("description", "").lower()
                new_desc = new_task["description"].lower()
                
                if self._text_similarity(existing_desc, new_desc) > 0.7:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                # Generate unique ID for task
                task_id = f"task-{len(existing_tasks) + 1}-{int(datetime.utcnow().timestamp())}"
                new_task["id"] = task_id
                new_task["status"] = "pending"
                existing_tasks.append(new_task)
        
        context.tasks = existing_tasks
    
    async def _update_goals(self, context: ChatContext, new_goals: List[str]) -> None:
        """Update context goals with new extracted goals"""
        if not new_goals:
            return
        
        # Use the most recent/specific goal as current goal
        if new_goals:
            most_specific_goal = max(new_goals, key=len)
            if len(most_specific_goal) > len(context.current_goal or ""):
                context.current_goal = most_specific_goal
    
    async def _update_summary(
        self, 
        context: ChatContext, 
        user_message: str, 
        assistant_response: str
    ) -> None:
        """Update problem summary based on conversation"""
        # Simple approach: if no summary exists, use parts of the first user message
        if not context.problem_summary and len(user_message) > 20:
            # Extract first sentence or first 150 characters
            sentences = re.split(r'[.!?]+', user_message)
            if sentences and len(sentences[0]) > 10:
                context.problem_summary = sentences[0].strip()
            else:
                context.problem_summary = user_message[:150].strip()
                if len(user_message) > 150:
                    context.problem_summary += "..."
        
        # Update timestamp
        context.updated_at = datetime.utcnow()
    
    async def extract_document_relevance(
        self, 
        context: ChatContext, 
        conversation_text: str, 
        available_documents: List[Dict[str, Any]]
    ) -> List[str]:
        """Determine which documents are relevant to the conversation"""
        relevant_docs = []
        
        conversation_lower = conversation_text.lower()
        
        for doc in available_documents:
            doc_id = doc.get("id", "")
            doc_title = doc.get("title", "").lower()
            doc_content = doc.get("content", "").lower()
            doc_tags = [tag.lower() for tag in doc.get("tags", [])]
            
            # Check for direct mentions
            if doc_title in conversation_lower or doc_id in conversation_lower:
                relevant_docs.append(doc_id)
                continue
            
            # Check for keyword matches
            conversation_words = set(re.findall(r'\w+', conversation_lower))
            doc_words = set(re.findall(r'\w+', doc_title + " " + " ".join(doc_tags)))
            
            # Calculate relevance score
            common_words = conversation_words.intersection(doc_words)
            if len(common_words) > 2:  # Threshold for relevance
                relevance_score = len(common_words) / len(doc_words) if doc_words else 0
                if relevance_score > 0.3:  # 30% word overlap threshold
                    relevant_docs.append(doc_id)
        
        return relevant_docs
    
    async def generate_context_insights(self, context: ChatContext) -> Dict[str, Any]:
        """Generate insights about the current context"""
        insights = {
            "task_summary": {
                "total": len(context.tasks or []),
                "completed": len([t for t in (context.tasks or []) if t.get("status") == "completed"]),
                "pending": len([t for t in (context.tasks or []) if t.get("status") == "pending"]),
                "high_priority": len([t for t in (context.tasks or []) if t.get("priority") == "high"])
            },
            "progress_percentage": 0,
            "next_suggested_action": None,
            "estimated_complexity": "medium"
        }
        
        # Calculate progress
        if insights["task_summary"]["total"] > 0:
            insights["progress_percentage"] = (
                insights["task_summary"]["completed"] / insights["task_summary"]["total"]
            ) * 100
        
        # Suggest next action
        pending_tasks = [t for t in (context.tasks or []) if t.get("status") == "pending"]
        if pending_tasks:
            # Prioritize high priority tasks
            high_priority_tasks = [t for t in pending_tasks if t.get("priority") == "high"]
            if high_priority_tasks:
                insights["next_suggested_action"] = high_priority_tasks[0]["description"]
            else:
                insights["next_suggested_action"] = pending_tasks[0]["description"]
        
        # Estimate complexity based on task count and content
        total_tasks = insights["task_summary"]["total"]
        if total_tasks <= 2:
            insights["estimated_complexity"] = "simple"
        elif total_tasks <= 5:
            insights["estimated_complexity"] = "medium"
        else:
            insights["estimated_complexity"] = "complex"
        
        return insights