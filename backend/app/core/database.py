from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, select
from typing import AsyncGenerator
import asyncio

from app.core.config import settings

# Create async engine
engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session
async_session_maker = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Create base class for models
Base = declarative_base()

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_db_and_tables():
    """Create database tables"""
    # Import all models here to ensure they are registered with SQLAlchemy
    from app.models import user, document, annotation
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create initial admin user if configured and doesn't exist
    await create_initial_admin()

async def create_initial_admin():
    """Create initial admin user if environment variables are set"""
    if not settings.ADMIN_USER_EMAIL or not settings.ADMIN_INITIAL_PASSWORD:
        print("No initial admin user configured - skipping admin creation")
        return
    
    from app.models.user import User
    from app.core.security import get_password_hash
    
    async with async_session_maker() as session:
        try:
            # Check if admin user already exists
            result = await session.execute(
                select(User).where(User.email == settings.ADMIN_USER_EMAIL)
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print(f"Admin user {settings.ADMIN_USER_EMAIL} already exists - skipping creation")
                return
            
            # Create initial admin user
            admin_user = User(
                email=settings.ADMIN_USER_EMAIL,
                name="Admin User",
                hashed_password=get_password_hash(settings.ADMIN_INITIAL_PASSWORD),
                password_reset_required=True,  # Must change password on first login
                is_admin=True,
                is_active=True,
                oauth_provider=None,
                oauth_id=None
            )
            
            session.add(admin_user)
            await session.commit()
            print(f"Created initial admin user: {settings.ADMIN_USER_EMAIL}")
            
        except Exception as e:
            print(f"Error creating initial admin user: {e}")
            await session.rollback()