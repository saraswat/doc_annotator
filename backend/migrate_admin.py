"""
Migration script to add admin functionality to existing database
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def migrate_admin_fields():
    """Add admin fields to existing users table"""
    
    # Get database URL from environment or use default
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db")
    
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            print("Checking current database schema...")
            
            # Check if columns already exist
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'hashed_password'
            """))
            
            if result.fetchone():
                print("✅ Admin fields already exist in database")
                return
            
            print("🔄 Adding admin fields to users table...")
            
            # 1. Make OAuth fields nullable (for password-based users)
            await conn.execute(text("ALTER TABLE users ALTER COLUMN oauth_provider DROP NOT NULL"))
            await conn.execute(text("ALTER TABLE users ALTER COLUMN oauth_id DROP NOT NULL"))
            print("  ✓ OAuth fields made nullable")
            
            # 2. Add password authentication fields
            await conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_required BOOLEAN DEFAULT FALSE"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR"))
            await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP"))
            print("  ✓ Password authentication fields added")
            
            # 3. Check if is_admin column exists, add if missing
            admin_check = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'is_admin'
            """))
            
            if not admin_check.fetchone():
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                print("  ✓ Admin role field added")
            else:
                print("  ✓ Admin role field already exists")
            
            print("✅ Database migration completed successfully!")
            print("🔄 You can now restart your system with admin environment variables")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        print(f"Full error: {traceback.format_exc()}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate_admin_fields())