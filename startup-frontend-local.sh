#!/bin/bash

# Local Frontend Startup Script  
# Starts the React frontend on localhost with HTTP

echo "🚀 Starting Document Annotation Frontend (Local Development)"
echo "==========================================================="

# Navigate to frontend directory
cd "$(dirname "$0")/frontend" || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Node modules not found. Installing dependencies..."
    npm install
fi

# Create or update .env.local for local development
echo "🔧 Setting up local environment configuration..."
cat > .env.local << EOF
# Local Development Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development

# Disable HTTPS for local development
HTTPS=false
HOST=localhost
PORT=3000

# Development settings
FAST_REFRESH=true
GENERATE_SOURCEMAP=true
EOF

echo "🔧 Configuration:"
echo "   - API URL: http://localhost:8000/api"
echo "   - Host: localhost"
echo "   - Port: 3000"
echo "   - Protocol: HTTP"
echo "   - HTTPS: Disabled"
echo "   - Hot Reload: Enabled"
echo ""

echo "🌐 Starting React development server..."
echo "   Frontend URL: http://localhost:3000"
echo "   Backend API: http://localhost:8000/api"
echo ""
echo "The browser should open automatically."
echo "Press Ctrl+C to stop the server"
echo ""

# Start the React development server
npm start