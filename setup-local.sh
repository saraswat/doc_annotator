#!/bin/bash

# Document Annotation System - Local Development Setup Script
# This script sets up the system to run locally without Docker
# Usage: ./setup-local.sh [DATABASE_TYPE]
# DATABASE_TYPE: postgresql (default), mysql, or sqlite

set -e

# Parse command line arguments
DATABASE_TYPE="${1:-postgresql}"

echo "🔧 Setting up Document Annotation System for local development..."
echo "🗄️ Database type: $DATABASE_TYPE"

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d " " -f 2 | cut -d "." -f 1,2)
if [ "$(printf '%s\n' "3.11" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.11" ]; then
    echo "⚠️ Warning: Python 3.11+ recommended (you have $PYTHON_VERSION)"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d "v" -f 2 | cut -d "." -f 1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "⚠️ Warning: Node.js 18+ recommended (you have v$NODE_VERSION)"
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    echo "⚠️ Warning: PostgreSQL CLI (psql) not found"
    echo "   Make sure PostgreSQL is installed and running"
fi

echo "✅ Prerequisites check completed"

# Set up database based on type
if [ "$DATABASE_TYPE" = "sqlite" ]; then
    echo "🗄️ Setting up SQLite database..."
    
    # Create data directory for SQLite database
    mkdir -p data
    
    # SQLite requires no additional setup - database file will be created automatically
    echo "✅ SQLite setup completed - database will be created automatically"
    
    DATABASE_URL="sqlite+aiosqlite:///./data/annotation.db"
elif [ "$DATABASE_TYPE" = "mysql" ]; then
    echo "🗄️ Setting up MySQL database..."
    
    # Check if MySQL is accessible
    if command -v mysql &> /dev/null; then
        echo "Creating MySQL user and database..."
        
        # Create database and user (ignore errors if already exist)
        mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS annotation_db;" 2>/dev/null || echo "Database annotation_db may already exist"
        mysql -u root -p -e "CREATE USER IF NOT EXISTS 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';" 2>/dev/null || echo "User annotation_user may already exist"
        mysql -u root -p -e "GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';" 2>/dev/null || true
        mysql -u root -p -e "FLUSH PRIVILEGES;" 2>/dev/null || true
        
        echo "✅ MySQL setup completed"
    else
        echo "⚠️ Warning: mysql not found in PATH"
        echo "   Please create the database manually:"
        echo "   mysql -u root -p -e \"CREATE DATABASE annotation_db;\""
        echo "   mysql -u root -p -e \"CREATE USER 'annotation_user'@'localhost' IDENTIFIED BY 'annotation_pass';\""
        echo "   mysql -u root -p -e \"GRANT ALL PRIVILEGES ON annotation_db.* TO 'annotation_user'@'localhost';\""
    fi
    
    DATABASE_URL="mysql+aiomysql://annotation_user:annotation_pass@localhost:3306/annotation_db"
else
    echo "🗄️ Setting up PostgreSQL database..."
    
    # Check if PostgreSQL is accessible
    if command -v psql &> /dev/null; then
        echo "Creating PostgreSQL user and database..."
        
        # Create user (ignore error if already exists)
        psql -d postgres -c "CREATE USER annotation_user WITH PASSWORD 'annotation_pass';" 2>/dev/null || echo "User annotation_user may already exist"
        
        # Create database (ignore error if already exists)  
        psql -d postgres -c "CREATE DATABASE annotation_db OWNER annotation_user;" 2>/dev/null || echo "Database annotation_db may already exist"
        
        # Grant privileges
        psql -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE annotation_db TO annotation_user;" 2>/dev/null || true
        psql -d annotation_db -c "GRANT ALL ON SCHEMA public TO annotation_user;" 2>/dev/null || true
        
        echo "✅ PostgreSQL setup completed"
    else
        echo "⚠️ Warning: psql not found in PATH"
        echo "   Please create the database manually:"
        echo "   createuser annotation_user"
        echo "   createdb -O annotation_user annotation_db"
    fi
    
    DATABASE_URL="postgresql+asyncpg://annotation_user:annotation_pass@localhost:5432/annotation_db"
fi

# Create .env file for backend
echo "📝 Creating backend environment configuration..."
cat > backend/.env << EOF
# Database Configuration
DATABASE_URL=$DATABASE_URL
DATABASE_TYPE=$DATABASE_TYPE

# Security
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Initial Admin User
ADMIN_USER_EMAIL=admin@test.com
ADMIN_INITIAL_PASSWORD=temppass123

# OAuth Configuration (optional)
OAUTH_PROVIDER=google
OAUTH_CLIENT_ID=
OAUTH_CLIENT_SECRET=
OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback

# CORS
CORS_ORIGINS=["http://localhost:3000"]

# Redis (optional)
REDIS_URL=redis://localhost:6379
EOF

# Create .env file for frontend
echo "📝 Creating frontend environment configuration..."
cat > frontend/.env << EOF
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000

# OAuth Configuration (optional)
REACT_APP_OAUTH_CLIENT_ID=
REACT_APP_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
EOF

# Set up backend
echo "🐍 Setting up Python backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Set up frontend
echo "⚛️ Setting up React frontend..."
cd frontend

echo "📦 Installing Node.js dependencies..."
npm install

cd ..

# Make startup scripts executable
chmod +x start-backend.sh
chmod +x start-frontend.sh

echo ""
echo "✅ Local development setup completed!"
echo ""
echo "📋 Next steps:"
if [ "$DATABASE_TYPE" = "sqlite" ]; then
    echo "   1. SQLite database will be created automatically in ./data/annotation.db"
elif [ "$DATABASE_TYPE" = "mysql" ]; then
    echo "   1. Make sure MySQL is running with a database named 'annotation_db'"
    echo "      If not created automatically, run the manual commands shown above"
else
    echo "   1. Make sure PostgreSQL is running with a database named 'annotation_db'"
    echo "      If not created automatically, run: createdb annotation_db"
fi
echo "   2. Start the backend: ./start-backend.sh [PORT] [DATABASE_TYPE]"
echo "   3. In another terminal, start the frontend: ./start-frontend.sh [FRONTEND_PORT] [BACKEND_PORT]"
echo "   4. Open http://localhost:3000 in your browser (or your custom port)"
echo ""
echo "🔧 Examples:"
echo "   PostgreSQL: ./start-backend.sh 8000 postgresql"
echo "   MySQL:      ./start-backend.sh 8000 mysql"
echo "   SQLite:     ./start-backend.sh 8000 sqlite"
echo "   Custom:     ./start-frontend.sh 3001 8080"
echo ""
echo "🔑 Default admin credentials:"
echo "   Email: admin@test.com"
echo "   Password: temppass123 (must be changed on first login)"
echo ""
echo "📁 Configuration files created:"
echo "   - backend/.env (backend configuration)"
echo "   - frontend/.env (frontend configuration)"
echo ""
echo "💡 To use OAuth, add your OAuth credentials to backend/.env"