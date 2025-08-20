#!/bin/bash

# Document Annotation System - Backend Startup Script (Production)
# This script sets up and starts the FastAPI backend with HTTPS
# Usage: ./start-backend.sh [PORT] [DATABASE_TYPE]
# Environment variables:
#   BACKEND_HOST - Host to bind to (default: read from env or 0.0.0.0)
#   SSL_KEYFILE - Path to SSL private key
#   SSL_CERTFILE - Path to SSL certificate
# Default port: 8000, default database: postgresql
# DATABASE_TYPE options: postgresql, mysql, sqlite

set -e

# Get configuration from environment variables
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${1:-8000}"
DATABASE_TYPE="${2:-postgresql}"

echo "🚀 Starting Document Annotation Backend..."
echo "🌐 Host: $BACKEND_HOST"
echo "🔌 Port: $BACKEND_PORT" 
echo "🗄️ Database type: $DATABASE_TYPE"

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
# Configure CORS origins based on environment
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
export CORS_ORIGINS="[\"https://$FRONTEND_HOST:3000\",\"https://$FRONTEND_HOST\",\"*\"]"
export OAUTH_CLIENT_ID="${OAUTH_CLIENT_ID:-}"
export OAUTH_CLIENT_SECRET="${OAUTH_CLIENT_SECRET:-}"
export OAUTH_PROVIDER="${OAUTH_PROVIDER:-google}"
export OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-https://$FRONTEND_HOST:3000/auth/callback}"

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

# SSL Configuration - Support both direct SSL and nginx SSL termination
SSL_KEYFILE="${SSL_KEYFILE:-./ssl/key.pem}"
SSL_CERTFILE="${SSL_CERTFILE:-./ssl/cert.pem}"
SSL_CA_CERTS="${SSL_CA_CERTS:-./ssl/ca.pem}"
USE_NGINX_SSL="${USE_NGINX_SSL:-false}"

echo "🔒 SSL Configuration:"
echo "  USE_NGINX_SSL: $USE_NGINX_SSL"
echo "  SSL_KEYFILE: $SSL_KEYFILE"
echo "  SSL_CERTFILE: $SSL_CERTFILE"
echo "  FRONTEND_HOST: $FRONTEND_HOST"

if [ "$USE_NGINX_SSL" = "true" ]; then
    # Nginx handles SSL termination - run backend as HTTP
    echo "🔄 Using nginx for SSL termination"
    echo "🌐 Starting FastAPI server with HTTP (nginx will handle HTTPS)..."
    echo "📋 Internal server URL: http://$BACKEND_HOST:$BACKEND_PORT"
    echo "📋 Public API URL: https://$BACKEND_HOST/api (via nginx)"
    echo "📋 API documentation: https://$BACKEND_HOST/docs (via nginx)"
    echo "🔴 Press Ctrl+C to stop the server"
    echo ""

    export HTTPS=false
    uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload
    
elif [ -f "$SSL_KEYFILE" ] && [ -f "$SSL_CERTFILE" ]; then
    # Direct SSL - run backend with SSL certificates
    echo "🌐 Starting FastAPI server with direct HTTPS..."
    echo "📋 Server URL: https://$BACKEND_HOST:$BACKEND_PORT"
    echo "📋 API documentation: https://$BACKEND_HOST:$BACKEND_PORT/docs"
    echo "🔴 Press Ctrl+C to stop the server"
    echo ""

    export HTTPS=true
    if [ -f "$SSL_CA_CERTS" ]; then
        echo "📋 Using CA certificate: $SSL_CA_CERTS"
        uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload --ssl-keyfile "$SSL_KEYFILE" --ssl-certfile "$SSL_CERTFILE" --ssl-ca-certs "$SSL_CA_CERTS"
    else
        uvicorn main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" --reload --ssl-keyfile "$SSL_KEYFILE" --ssl-certfile "$SSL_CERTFILE"
    fi
else
    echo "❌ SSL configuration missing!"
    echo ""
    echo "Choose one of these options:"
    echo "1. Use nginx for SSL termination:"
    echo "   export USE_NGINX_SSL=true"
    echo "   ./start-backend.sh"
    echo ""
    echo "2. Use direct SSL certificates:"
    echo "   Create SSL certificates at:"
    echo "     SSL_KEYFILE: $SSL_KEYFILE"
    echo "     SSL_CERTFILE: $SSL_CERTFILE"
    echo ""
    echo "3. For local development:"
    echo "   ./startup-backend-local.sh"
    echo ""
    exit 1
fi
