#!/bin/bash

# Document Annotation System - Backend Startup Script
# This script sets up and starts the FastAPI backend without Docker
# Usage: ./start-backend.sh [PORT]
# Default port: 8000

set -e

# Parse command line arguments
BACKEND_PORT="${1:-8000}"

echo "🚀 Starting Document Annotation Backend on port $BACKEND_PORT..."

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
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db}"
export SECRET_KEY="${SECRET_KEY:-$(python -c 'import secrets; print(secrets.token_hex(32))')}"
export ADMIN_USER_EMAIL="${ADMIN_USER_EMAIL:-admin@test.com}"
export ADMIN_INITIAL_PASSWORD="${ADMIN_INITIAL_PASSWORD:-temppass123}"
export CORS_ORIGINS='["http://localhost:3000"]'
export OAUTH_CLIENT_ID="${OAUTH_CLIENT_ID:-}"
export OAUTH_CLIENT_SECRET="${OAUTH_CLIENT_SECRET:-}"
export OAUTH_PROVIDER="${OAUTH_PROVIDER:-google}"
export OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-http://localhost:3000/auth/callback}"

echo "🗄️ Environment Configuration:"
echo "  DATABASE_URL: $DATABASE_URL"
echo "  ADMIN_USER_EMAIL: $ADMIN_USER_EMAIL"
echo "  CORS_ORIGINS: $CORS_ORIGINS"

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL connection..."
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

if [ $? -ne 0 ]; then
    exit 1
fi

# Start the FastAPI server
echo "🌐 Starting FastAPI server on http://localhost:$BACKEND_PORT..."
echo "📋 API documentation will be available at http://localhost:$BACKEND_PORT/docs"
echo "🔴 Press Ctrl+C to stop the server"
echo ""

# Update CORS origins to include frontend with any port
export CORS_ORIGINS='["http://localhost:3000", "http://localhost:3001", "http://localhost:8080"]'

uvicorn main:app --host 0.0.0.0 --port $BACKEND_PORT --reload