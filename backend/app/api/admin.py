from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_async_session
from app.core.security import get_current_admin_user, get_password_hash, generate_password_reset_token
from app.models.user import User
from app.models.document import Document
from app.schemas.user import UserResponse, UserCreateByAdmin, UserPasswordReset

router = APIRouter()

@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all users (admin only)"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [UserResponse.from_orm(user) for user in users]

@router.post("/users", response_model=UserResponse)
async def create_user_by_admin(
    user_data: UserCreateByAdmin,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new user with password (admin only)"""
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name,
        avatar_url=user_data.avatar_url,
        hashed_password=get_password_hash(user_data.password),
        password_reset_required=True,  # User must change password on first login
        is_admin=user_data.is_admin or False,
        oauth_provider=None,  # Password-based user
        oauth_id=None
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: UserPasswordReset,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Reset a user's password (admin only)"""
    # Get the user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(password_data.new_password)
    user.password_reset_required = True
    user.password_reset_token = None
    user.password_reset_expires = None
    
    await db.commit()
    await db.refresh(user)
    
    return {"message": "Password reset successfully", "user_id": user_id}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a user (admin only)"""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own admin account"
        )
    
    # Check if user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    
    return {"message": "User deleted successfully", "user_id": user_id}

@router.get("/documents")
async def get_all_documents(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Get all documents (admin only)"""
    result = await db.execute(select(Document))
    documents = result.scalars().all()
    
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "filename": doc.filename,
            "file_type": doc.document_type.value if doc.document_type else "unknown",
            "key": doc.document_key,
            "date": doc.document_date,
            "owner_id": doc.owner_id,
            "created_at": doc.created_at,
            "file_size": doc.file_size,
            "is_public": doc.is_public
        }
        for doc in documents
    ]

@router.patch("/documents/{document_id}/toggle-public")
async def toggle_document_public(
    document_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Toggle document public status (admin only)"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Toggle the public status
    document.is_public = not document.is_public
    await db.commit()
    
    return {
        "message": f"Document {'made public' if document.is_public else 'made private'}",
        "is_public": document.is_public
    }

@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Delete a document (admin only)"""
    # Check if document exists
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete document
    await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()
    
    return {"message": "Document deleted successfully", "document_id": document_id}