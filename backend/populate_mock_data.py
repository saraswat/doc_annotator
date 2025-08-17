#!/usr/bin/env python3
"""
Script to populate the database with mock documents for testing.
Run this script after the application is running to add sample documents.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_async_session
from app.models.user import User
from app.models.document import Document, DocumentType
from sqlalchemy import select


async def populate_documents():
    """Populate the database with mock documents."""
    
    # Get database session
    async for session in get_async_session():
        try:
            # Get the first user (should be the OAuth user)
            result = await session.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            
            if not user:
                print("No users found in database. Please sign in first to create a user.")
                return
            
            print(f"Creating documents for user: {user.name} ({user.email})")
            
            # Define mock documents with their file paths
            mock_documents = [
                {
                    "title": "Q4 2024 Business Performance Report",
                    "filename": "sample_report.html",
                    "description": "Comprehensive quarterly report showing 25% revenue growth and market expansion achievements.",
                    "file_path": "mock_documents/sample_report.html",
                    "document_type": DocumentType.HTML,
                    "file_size": 15420
                },
                {
                    "title": "RESTful API Technical Specification v2.1",
                    "filename": "technical_specification.html", 
                    "description": "Complete technical documentation for our REST API including endpoints, authentication, and error handling.",
                    "file_path": "mock_documents/technical_specification.html",
                    "document_type": DocumentType.HTML,
                    "file_size": 28350
                },
                {
                    "title": "Next-Generation Document Collaboration Platform Proposal",
                    "filename": "project_proposal.md",
                    "description": "Project proposal for building a revolutionary document collaboration platform with AI-powered features.",
                    "file_path": "mock_documents/project_proposal.md", 
                    "document_type": DocumentType.MARKDOWN,
                    "file_size": 18750
                },
                {
                    "title": "Weekly Team Standup Notes - Feb 15, 2025",
                    "filename": "meeting_notes.md",
                    "description": "Sprint progress updates, blockers, and action items from the weekly team standup meeting.",
                    "file_path": "mock_documents/meeting_notes.md",
                    "document_type": DocumentType.MARKDOWN,
                    "file_size": 12340
                },
                {
                    "title": "Advanced ML Techniques for Document Processing",
                    "filename": "research_paper.html",
                    "description": "Research paper on hybrid neural architectures combining transformers and CNNs for document analysis.",
                    "file_path": "mock_documents/research_paper.html",
                    "document_type": DocumentType.HTML,
                    "file_size": 34680
                }
            ]
            
            # Check if documents already exist
            result = await session.execute(select(Document))
            existing_documents = result.scalars().all()
            
            if existing_documents:
                print(f"Found {len(existing_documents)} existing documents. Skipping creation.")
                return
            
            # Create documents
            created_count = 0
            for doc_data in mock_documents:
                # Check if file exists
                file_path = Path(__file__).parent / doc_data["file_path"]
                if not file_path.exists():
                    print(f"Warning: File not found: {file_path}")
                    continue
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Create document
                document = Document(
                    title=doc_data["title"],
                    filename=doc_data["filename"],
                    description=doc_data["description"],
                    content=content,
                    file_path=doc_data["file_path"],
                    file_size=doc_data["file_size"],
                    document_type=doc_data["document_type"],
                    owner_id=user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                session.add(document)
                created_count += 1
                print(f"✅ Created: {doc_data['title']}")
            
            # Commit all documents
            await session.commit()
            print(f"\n🎉 Successfully created {created_count} mock documents!")
            
        except Exception as e:
            print(f"❌ Error creating documents: {str(e)}")
            await session.rollback()
        finally:
            await session.close()


if __name__ == "__main__":
    print("🚀 Starting mock document population...")
    asyncio.run(populate_documents())
    print("✨ Done!")