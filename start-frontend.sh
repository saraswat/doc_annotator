#!/bin/bash

# Document Annotation System - Frontend Startup Script (Production)
# This script sets up and starts the React frontend with HTTPS
# Usage: ./start-frontend.sh [PORT] [BACKEND_PORT]
# Environment variables:
#   FRONTEND_HOST - Host to bind to (default: read from env or localhost)
#   BACKEND_HOST - Backend host to connect to (default: read from env or localhost)
# Default ports: frontend=3000, backend=8000

set -e

# Get configuration from environment variables
FRONTEND_HOST="${FRONTEND_HOST:-localhost}"
BACKEND_HOST="${BACKEND_HOST:-localhost}"
FRONTEND_PORT="${1:-3000}"
BACKEND_PORT="${2:-8000}"

echo "🚀 Starting Document Annotation Frontend..."
echo "🌐 Frontend Host: $FRONTEND_HOST"
echo "🔌 Frontend Port: $FRONTEND_PORT"
echo "🔗 Backend Host: $BACKEND_HOST"
echo "🔌 Backend Port: $BACKEND_PORT"

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

# Set environment variables for production deployment
echo "⚙️ Setting environment variables for production..."

# Support nginx SSL termination - frontend makes HTTPS requests to nginx
USE_NGINX_SSL="${USE_NGINX_SSL:-false}"
if [ "$USE_NGINX_SSL" = "true" ]; then
    # Nginx handles SSL - API calls go to public HTTPS endpoints
    export REACT_APP_API_URL="https://$BACKEND_HOST/api"
    export REACT_APP_WS_URL="wss://$BACKEND_HOST"
else
    # Direct connection to backend (with port)
    export REACT_APP_API_URL="https://$BACKEND_HOST:$BACKEND_PORT/api"
    export REACT_APP_WS_URL="wss://$BACKEND_HOST:$BACKEND_PORT"
fi

export PORT="$FRONTEND_PORT"
export HOST="$FRONTEND_HOST"

echo "🗄️ Environment Configuration:"
echo "  Frontend Port: $FRONTEND_PORT"
echo "  Frontend Host: $HOST"
echo "  Backend Host: $BACKEND_HOST"
echo "  Backend Port: $BACKEND_PORT"
echo "  REACT_APP_API_URL: $REACT_APP_API_URL"
echo "  REACT_APP_WS_URL: $REACT_APP_WS_URL"

# Check backend connectivity based on SSL configuration
echo "🔍 Checking backend connection..."
echo "  USE_NGINX_SSL: $USE_NGINX_SSL"

if [ "$USE_NGINX_SSL" = "true" ]; then
    # Check public HTTPS endpoint (nginx)
    if curl -k -s "https://$BACKEND_HOST/health" > /dev/null; then
        echo "✅ Backend is accessible via nginx HTTPS"
    else
        echo "❌ Backend is not accessible via nginx HTTPS"
        echo "💡 Make sure nginx is configured and backend is running"
        echo "💡 Start backend with: USE_NGINX_SSL=true ./start-backend.sh"
        exit 1
    fi
else
    # Check direct HTTPS connection to backend
    if curl -k -s "https://$BACKEND_HOST:$BACKEND_PORT/health" > /dev/null; then
        echo "✅ Backend is running with direct HTTPS"
    else
        echo "❌ Backend is not accessible via direct HTTPS"
        echo "💡 Make sure to start the backend first with: ./start-backend.sh $BACKEND_PORT"
        exit 1
    fi
fi

# SSL Configuration for frontend
SSL_KEYFILE="${SSL_KEYFILE:-./frontend/ssl/key.pem}"
SSL_CERTFILE="${SSL_CERTFILE:-./frontend/ssl/cert.pem}"

echo "🔒 Frontend SSL Configuration:"
echo "  USE_NGINX_SSL: $USE_NGINX_SSL"
echo "  SSL_KEYFILE: $SSL_KEYFILE"
echo "  SSL_CERTFILE: $SSL_CERTFILE"

if [ "$USE_NGINX_SSL" = "true" ]; then
    # Nginx handles SSL for frontend too - run as HTTP
    echo "🔄 Using nginx for frontend SSL termination"
    echo "🌐 Starting React server with HTTP (nginx will handle HTTPS)..."
    echo "📋 Internal frontend URL: http://$FRONTEND_HOST:$FRONTEND_PORT"
    echo "📋 Public frontend URL: https://$FRONTEND_HOST (via nginx)"
    echo "🔴 Press Ctrl+C to stop the server"
    echo ""
    
    export HTTPS=false
    npm start
    
elif [ -f "$SSL_KEYFILE" ] && [ -f "$SSL_CERTFILE" ]; then
    # Direct SSL for frontend
    export HTTPS=true
    export SSL_CRT_FILE="$SSL_CERTFILE"
    export SSL_KEY_FILE="$SSL_KEYFILE"
    echo "🌐 Starting React server with direct HTTPS..."
    echo "📋 Frontend URL: https://$FRONTEND_HOST:$FRONTEND_PORT"
    echo "🔴 Press Ctrl+C to stop the server"
    echo ""
    npm start
else
    echo "❌ SSL configuration missing!"
    echo ""
    echo "Choose one of these options:"
    echo "1. Use nginx for SSL termination:"
    echo "   export USE_NGINX_SSL=true"
    echo "   ./start-frontend.sh"
    echo ""
    echo "2. Use direct SSL certificates:"
    echo "   Create SSL certificates at:"
    echo "     SSL_KEYFILE: $SSL_KEYFILE"
    echo "     SSL_CERTFILE: $SSL_CERTFILE"
    echo ""
    echo "3. For local development:"
    echo "   ./startup-frontend-local.sh"
    echo ""
    exit 1
fi
