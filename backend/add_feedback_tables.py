#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the parent directory to Python path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_async_session
from app.core.database_config import engine

async def create_feedback_tables():
    """Create the message_feedback table."""
    
    create_feedback_table_sql = """
    CREATE TABLE IF NOT EXISTS message_feedback (
        id VARCHAR(36) PRIMARY KEY,
        message_id VARCHAR(36) NOT NULL,
        session_id VARCHAR(36) NOT NULL,
        user_id INTEGER NOT NULL,
        feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down')),
        message_order INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(message_id),
        FOREIGN KEY (message_id) REFERENCES chat_messages(id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    
    create_feedback_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);",
        "CREATE INDEX IF NOT EXISTS idx_message_feedback_session_id ON message_feedback(session_id);",
        "CREATE INDEX IF NOT EXISTS idx_message_feedback_user_id ON message_feedback(user_id);"
    ]
    
    async with engine.begin() as conn:
        try:
            print("Creating message_feedback table...")
            await conn.execute(text(create_feedback_table_sql))
            
            print("Creating indexes for message_feedback...")
            for index_sql in create_feedback_indexes:
                await conn.execute(text(index_sql))
            
            print("✅ Message feedback tables created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(create_feedback_tables())