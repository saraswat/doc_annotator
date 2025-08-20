"""
Migration script to add chat tables to the database.
Run this script to create the chat_sessions, chat_messages, and chat_contexts tables.
"""

import asyncio
from app.core.database_config import engine, Base
from app.models.chat import ChatSession, ChatMessage, ChatContext

async def create_chat_tables():
    """Create chat-related tables in the database."""
    print("Creating chat tables...")
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Chat tables created successfully!")
        print("Tables added:")
        print("  - chat_sessions")
        print("  - chat_messages") 
        print("  - chat_contexts")
        
    except Exception as e:
        print(f"❌ Error creating chat tables: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(create_chat_tables())