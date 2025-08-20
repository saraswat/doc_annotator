#!/bin/bash

# Local Backend Startup Script
# Starts the FastAPI backend on localhost with HTTP

echo "🚀 Starting Document Annotation Backend (Local Development)"
echo "========================================================="

# Navigate to backend directory
cd "$(dirname "$0")/backend" || exit 1

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Set local development environment variables
export DATABASE_TYPE=sqlite
export DATABASE_URL=sqlite+aiosqlite:///./data/annotation.db
export CORS_ORIGINS='["http://localhost:3000", "http://127.0.0.1:3000"]'

# Create data directory if it doesn't exist
mkdir -p data

echo "🔧 Configuration:"
echo "   - Database: SQLite (local file)"
echo "   - Host: localhost"
echo "   - Port: 8000"
echo "   - Protocol: HTTP"
echo "   - CORS: Enabled for localhost:3000"
echo ""

# Start the backend server
echo "🌐 Starting FastAPI server..."
echo "   Backend URL: http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start uvicorn with local development settings
python -m uvicorn main:app \
    --host localhost \
    --port 8000 \
    --reload \
    --reload-dir app \
    --log-level info \
    --access-log