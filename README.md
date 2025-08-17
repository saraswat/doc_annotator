# Document Annotator

A modern web application for annotating and managing documents with support for PDF, HTML, Markdown, and text files. Built with React, TypeScript, FastAPI, and PostgreSQL.

## Features

### Document Management
- **Multi-format Support**: PDF, HTML, Markdown, and text files
- **Organized Storage**: Documents organized by key/date combinations for easy categorization
- **Bulk Upload**: Upload entire directory structures or archive files (ZIP/TAR)
- **Single Upload**: Upload individual documents with custom key/date classification
- **Auto-refresh**: Document lists update automatically when new files are uploaded
- **Smart Navigation**: Auto-open single documents, show selection for multiple documents

### Annotation System
- **Universal Text Selection**: Select any text in documents to create annotations
- **Cross-format Compatibility**: Annotations work consistently across PDF, HTML, and Markdown
- **Visual Highlighting**: Selected text highlighted with customizable colors and hover effects
- **Comment Management**: Add, view, and delete annotations with full context
- **Document Comments**: Add general comments not tied to specific text selections
- **Click Navigation**: Click annotations to scroll to highlighted text in main pane
- **Real-time Updates**: Annotations update immediately across the interface

### PDF-Specific Features
- **High-performance Rendering**: Uses react-pdf-selection for optimized PDF display
- **Coordinate-based Annotations**: Precise positioning using PDF coordinate systems
- **Page Navigation**: Click annotation cards to jump to specific pages
- **Scalable Display**: Optimized rendering performance for large PDF documents

### HTML & Markdown Features
- **DOM-based Highlighting**: Direct text highlighting in rendered content
- **Character Offset Tracking**: Precise text positioning using character offsets
- **Scroll-to-text**: Click annotations to scroll to exact text location
- **Real-time Cleanup**: Highlights removed immediately when annotations are deleted

### User Interface
- **Responsive Design**: Clean, modern interface that works on all screen sizes
- **Three-pane Layout**: Document browser, main content viewer, and annotation sidebar
- **Google OAuth**: Secure authentication with Google accounts
- **Material-UI**: Accessible, professional interface components
- **Real-time Feedback**: Loading states, progress indicators, and status updates

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the project directory
2. Copy environment files:
   ```bash
   cp .env.example .env
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
3. Update OAuth credentials in the .env files
4. Start all services:
   ```bash
   docker-compose up --build
   ```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- API Documentation: http://localhost:8001/docs

### Manual Development Setup

#### Backend
```bash
cd backend
source ~/anaconda3/etc/profile.d/conda.sh
conda activate py312-lmc
pip install -r requirements.txt
uvicorn main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
doc_annotator/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── core/     # Configuration and database
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   ├── uploads/      # Document storage
├── frontend/         # React frontend
│   └── src/
│       ├── components/
│       ├── contexts/
│       └── services/
└── docker-compose.yml
```

## Configuration

Set up OAuth with your preferred provider (Google, Azure, Okta) and update the environment variables accordingly. See the react-fastapi-instructions.md file for detailed setup steps.

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis, Socket.IO
- **Frontend**: React 18, TypeScript, Material-UI, Socket.IO Client
- **Authentication**: OAuth 2.0 (Google, Azure, Okta)
- **Real-time**: WebSocket with Socket.IO
- **Database**: PostgreSQL with async SQLAlchemy
- **Caching**: Redis

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.