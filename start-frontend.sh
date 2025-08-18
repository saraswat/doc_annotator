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
export REACT_APP_API_URL="https://localhost:$BACKEND_PORT/api"
export REACT_APP_WS_URL="wss://localhost:$BACKEND_PORT"
export PORT="$FRONTEND_PORT"
export HOST="0.0.0.0"

echo "🗄️ Environment Configuration:"
echo "  Frontend Port: $FRONTEND_PORT"
echo "  Frontend Host: $HOST"
echo "  Backend Port: $BACKEND_PORT"
echo "  REACT_APP_API_URL: $REACT_APP_API_URL"
echo "  REACT_APP_WS_URL: $REACT_APP_WS_URL"

# Check if backend is running (try HTTPS first, then HTTP)
echo "🔍 Checking backend connection..."
if curl -k -s "https://localhost:$BACKEND_PORT/health" > /dev/null; then
    echo "✅ Backend is running and accessible via HTTPS"
elif curl -s "http://localhost:$BACKEND_PORT/health" > /dev/null; then
    echo "✅ Backend is running via HTTP"
    echo "⚠️ Consider generating SSL certificates for HTTPS: ./generate-ssl-certs.sh"
else
    echo "⚠️ Warning: Backend may not be running on localhost:$BACKEND_PORT"
    echo "💡 Make sure to start the backend first with ./start-backend.sh $BACKEND_PORT"
fi

# Check if we need HTTPS for frontend
HTTPS_REQUIRED="${HTTPS:-false}"
if [ -f "./ssl/cert.pem" ] && [ -f "./ssl/key.pem" ]; then
    export HTTPS=true
    export SSL_CRT_FILE="./ssl/cert.pem"
    export SSL_KEY_FILE="./ssl/key.pem"
    echo "🌐 Starting React development server with HTTPS on https://localhost:$FRONTEND_PORT..."
else
    echo "🌐 Starting React development server on http://localhost:$FRONTEND_PORT..."
    echo "💡 For HTTPS frontend, run: ./generate-ssl-certs.sh"
fi
echo "🔴 Press Ctrl+C to stop the server"
echo ""

npm start