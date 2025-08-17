#!/bin/bash

# Document Annotation System - Frontend Startup Script  
# This script sets up and starts the React frontend without Docker
# Usage: ./start-frontend.sh [PORT] [BACKEND_PORT]
# Default ports: frontend=3000, backend=8000

set -e

# Parse command line arguments
FRONTEND_PORT="${1:-3000}"
BACKEND_PORT="${2:-8000}"

echo "🚀 Starting Document Annotation Frontend on port $FRONTEND_PORT..."
echo "🔗 Connecting to backend on port $BACKEND_PORT..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Change to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
else
    echo "✅ Node.js dependencies already installed"
fi

# Set environment variables
echo "⚙️ Setting environment variables..."
export REACT_APP_API_URL="http://localhost:$BACKEND_PORT/api"
export REACT_APP_WS_URL="ws://localhost:$BACKEND_PORT"
export PORT="$FRONTEND_PORT"

echo "🗄️ Environment Configuration:"
echo "  Frontend Port: $FRONTEND_PORT"
echo "  Backend Port: $BACKEND_PORT"
echo "  REACT_APP_API_URL: $REACT_APP_API_URL"
echo "  REACT_APP_WS_URL: $REACT_APP_WS_URL"

# Check if backend is running
echo "🔍 Checking backend connection..."
if curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
    echo "✅ Backend is running and accessible"
else
    echo "⚠️ Warning: Backend may not be running on http://localhost:$BACKEND_PORT"
    echo "💡 Make sure to start the backend first with ./start-backend.sh $BACKEND_PORT"
fi

# Start the React development server
echo ""
echo "🌐 Starting React development server on http://localhost:$FRONTEND_PORT..."
echo "🔴 Press Ctrl+C to stop the server"
echo ""

npm start