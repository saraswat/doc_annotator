from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, select
from typing import AsyncGenerator
import asyncio
import re

from app.core.config import settings

def get_database_url_and_engine():
    """
    Get the appropriate database URL and create async engine based on DATABASE_TYPE
    """
    database_type = settings.DATABASE_TYPE.lower()
    database_url = settings.DATABASE_URL
    
    if database_type == "sqlite":
        # Convert other database URLs to SQLite format if needed
        if "postgresql" in database_url or "mysql" in database_url:
            database_url = "sqlite+aiosqlite:///./data/annotation.db"
        
        # Ensure it's using the async SQLite driver
        if "sqlite://" in database_url and "sqlite+aiosqlite://" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        # SQLite-specific engine configuration
        engine = create_async_engine(
            database_url,
            echo=True,
            pool_pre_ping=True,
            # SQLite-specific settings
            connect_args={
                "check_same_thread": False,
            }
        )
        
    elif database_type == "mysql":
        # Convert PostgreSQL URL to MySQL format if needed
        if "postgresql" in database_url:
            # Extract components from PostgreSQL URL
            match = re.match(r'postgresql\+asyncpg://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
            if match:
                user, password, host, port, database = match.groups()
                database_url = f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}"
        
        # Ensure it's using the async MySQL driver
        if "mysql://" in database_url and "mysql+aiomysql://" not in database_url:
            database_url = database_url.replace("mysql://", "mysql+aiomysql://")
        
        # MySQL-specific engine configuration
        engine = create_async_engine(
            database_url,
            echo=True,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
            # MySQL-specific settings
            connect_args={
                "charset": "utf8mb4",
                "autocommit": False,
            }
        )
        
    else:  # Default to PostgreSQL
        # Ensure it's using the async PostgreSQL driver
        if "postgresql://" in database_url and "postgresql+asyncpg://" not in database_url:
            database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        # PostgreSQL-specific engine configuration
        engine = create_async_engine(
            database_url,
            echo=True,
            pool_size=20,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
        )
    
    print(f"Using database: {database_type}")
    print(f"Database URL: {database_url.split('@')[0] if '@' in database_url else database_url}")
    
    return database_url, engine

# Create async engine based on configuration
database_url, engine = get_database_url_and_engine()

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