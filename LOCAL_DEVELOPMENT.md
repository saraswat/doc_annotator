# Local Development Setup

This guide explains how to run the Document Annotation System locally for development.

## Quick Start

### 1. Start Backend Server
```bash
./startup-backend-local.sh
```

### 2. Start Frontend Server (in another terminal)
```bash
./startup-frontend-local.sh
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## What These Scripts Do

### Backend Script (`startup-backend-local.sh`)
- Activates Python virtual environment
- Installs dependencies if needed
- Sets up SQLite database for local development
- Configures CORS for localhost:3000
- Starts FastAPI server on `localhost:8000` with HTTP
- Enables auto-reload for development

### Frontend Script (`startup-frontend-local.sh`)
- Installs Node.js dependencies if needed
- Creates `.env.local` with local development configuration
- Sets API URL to `http://localhost:8000/api`
- Disables HTTPS for local development
- Starts React dev server on `localhost:3000`
- Enables hot reload and source maps

## Environment Configuration

### Backend (.env)
The backend uses the existing `.env` file with local development defaults:
- SQLite database (file-based, no external DB required)
- CORS enabled for localhost
- Development logging enabled

### Frontend (.env.local)
The frontend script automatically creates `.env.local` with:
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
HTTPS=false
HOST=localhost
PORT=3000
```

## Chat System Setup

To use the chat functionality, you need to add an LLM API key to the backend `.env` file:

```env
# Add one of these API keys:
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Prerequisites

### Backend
- Python 3.8+
- Virtual environment set up (`python -m venv venv`)
- Dependencies installed (`pip install -r requirements.txt`)

### Frontend
- Node.js 16+
- npm or yarn

## Troubleshooting

### Port Already in Use
If ports 3000 or 8000 are already in use:

**Backend (port 8000):**
- Kill existing process: `lsof -ti:8000 | xargs kill -9`
- Or modify the script to use a different port

**Frontend (port 3000):**
- The React dev server will automatically suggest an alternative port
- Or set `PORT=3001` in the script

### CORS Issues
If you get CORS errors:
- Ensure the backend CORS_ORIGINS includes your frontend URL
- Check that you're using HTTP (not HTTPS) for both services

### Database Issues
- The SQLite database file is created automatically in `backend/data/`
- To reset: delete `backend/data/annotation.db` and restart backend

## Development Workflow

1. Start backend server first
2. Start frontend server in a separate terminal
3. Make changes to code - both servers auto-reload
4. Access API docs at http://localhost:8000/docs for backend testing
5. Use browser dev tools for frontend debugging

## Production Deployment

These scripts are for **local development only**. For production deployment:
- Use HTTPS
- Use a production database (PostgreSQL recommended)  
- Set proper environment variables
- Use production build for frontend
- Configure proper CORS origins