#!/bin/bash

# Document Annotation System - Backend Startup Script
# This script sets up and starts the FastAPI backend without Docker
# Usage: ./start-backend.sh [PORT] [DATABASE_TYPE]
# Default port: 8000, default database: postgresql
# DATABASE_TYPE options: postgresql, mysql, sqlite

set -e

# Parse command line arguments
BACKEND_PORT="${1:-8000}"
DATABASE_TYPE="${2:-postgresql}"

echo "🚀 Starting Document Annotation Backend on port $BACKEND_PORT..."
echo "🗄️ Using database type: $DATABASE_TYPE"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Set required environment variables
echo "⚙️ Setting environment variables..."

# Configure database URL based on type
if [ "$DATABASE_TYPE" = "sqlite" ]; then
    # Create data directory if it doesn't exist
    mkdir -p data
    export DATABASE_URL="${DATABASE_URL:-sqlite+aiosqlite:///./data/annotation.db}"
    export DATABASE_TYPE="sqlite"
elif [ "$DATABASE_TYPE" = "mysql" ]; then
    export DATABASE_URL="${DATABASE_URL:-mysql+aiomysql://annotation_user:annotation_pass@localhost:3306/annotation_db}"
    export DATABASE_TYPE="mysql"
else
    export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db}"
    export DATABASE_TYPE="postgresql"
fi

export SECRET_KEY="${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"
export ADMIN_USER_EMAIL="${ADMIN_USER_EMAIL:-admin@test.com}"
export ADMIN_INITIAL_PASSWORD="${ADMIN_INITIAL_PASSWORD:-temppass123}"
export CORS_ORIGINS='["https://localhost:3000"]'
export OAUTH_CLIENT_ID="${OAUTH_CLIENT_ID:-}"
export OAUTH_CLIENT_SECRET="${OAUTH_CLIENT_SECRET:-}"
export OAUTH_PROVIDER="${OAUTH_PROVIDER:-google}"
export OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-https://localhost:3000/auth/callback}"

echo "🗄️ Environment Configuration:"
echo "  DATABASE_TYPE: $DATABASE_TYPE"
echo "  DATABASE_URL: $(echo $DATABASE_URL | sed 's/:.*@/:***@/')"
echo "  ADMIN_USER_EMAIL: $ADMIN_USER_EMAIL"
echo "  CORS_ORIGINS: $CORS_ORIGINS"

# Check database connection
echo "🔍 Checking $DATABASE_TYPE connection..."

if [ "$DATABASE_TYPE" = "sqlite" ]; then
    python -c "
import aiosqlite
import asyncio
import sys
import os

async def check_db():
    try:
        # For SQLite, just check if we can connect to the database
        db_path = './data/annotation.db'
        
        # Create directory if it doesn't exist
        os.makedirs('./data', exist_ok=True)
        
        async with aiosqlite.connect(db_path) as conn:
            await conn.execute('SELECT 1')
            await conn.commit()
        
        print('✅ SQLite connection successful')
        print(f'📁 Database location: {os.path.abspath(db_path)}')
        return True
    except Exception as e:
        print(f'❌ SQLite connection failed: {e}')
        return False

if not asyncio.run(check_db()):
    sys.exit(1)
"
elif [ "$DATABASE_TYPE" = "mysql" ]; then
    python -c "
import aiomysql
import asyncio
import sys
import re

async def check_db():
    try:
        # Extract connection details from DATABASE_URL
        url = '$DATABASE_URL'
        match = re.match(r'mysql\+aiomysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', url)
        if match:
            user, password, host, port, database = match.groups()
            conn = await aiomysql.connect(
                host=host, port=int(port), user=user, password=password, db=database
            )
            conn.close()
            print('✅ MySQL connection successful')
            return True
        else:
            print('❌ Invalid MySQL DATABASE_URL format')
            return False
    except Exception as e:
        print(f'❌ MySQL connection failed: {e}')
        print('💡 Make sure MySQL is running and the database exists')
        print('   You can create the database with:')
        print('   mysql -u root -p -e \"CREATE DATABASE annotation_db;\"')
        print('   mysql -u root -p -e \"CREATE USER annotation_user@localhost IDENTIFIED BY \\'annotation_pass\\';\"')
        print('   mysql -u root -p -e \"GRANT ALL ON annotation_db.* TO annotation_user@localhost;\"')
        return False

if not asyncio.run(check_db()):
    sys.exit(1)
"
else
    python -c "
import asyncpg
import asyncio
import sys

async def check_db():
    try:
        # Extract connection details from DATABASE_URL
        url = '$DATABASE_URL'
        if 'postgresql+asyncpg://' in url:
            url = url.replace('postgresql+asyncpg://', 'postgresql://')
        
        conn = await asyncpg.connect(url)
        await conn.close()
        print('✅ PostgreSQL connection successful')
        return True
    except Exception as e:
        print(f'❌ PostgreSQL connection failed: {e}')
        print('💡 Make sure PostgreSQL is running and the database exists')
        print('   You can create the database with:')
        print('   createdb annotation_db')
        return False

if not asyncio.run(check_db()):
    sys.exit(1)
"
fi

if [ $? -ne 0 ]; then
    exit 1
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:$BACKEND_PORT..."
echo "📋 API documentation will be available at http://localhost:$BACKEND_PORT/docs"
echo "🔴 Press Ctrl+C to stop the server"
echo ""

# Update CORS origins to include frontend with any port
export CORS_ORIGINS='["https://localhost:3000", "https://localhost:3001", "https://localhost:8080"]'

# SSL certificates for HTTPS
SSL_KEYFILE="${SSL_KEYFILE:-./ssl/key.pem}"
SSL_CERTFILE="${SSL_CERTFILE:-./ssl/cert.pem}"

# Start with HTTPS if certificates exist, otherwise HTTP
if [ -f "$SSL_KEYFILE" ] && [ -f "$SSL_CERTFILE" ]; then
    echo "🔒 Starting with HTTPS using SSL certificates"
    uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload --ssl-keyfile "$SSL_KEYFILE" --ssl-certfile "$SSL_CERTFILE"
else
    echo "⚠️ SSL certificates not found at $SSL_KEYFILE and $SSL_CERTFILE"
    echo "🔓 Starting with HTTP (not recommended for production)"
    uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload
fi