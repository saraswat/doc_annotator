# Feature Documentation

## Core Features

### 1. Document Upload and Management

#### Bulk Upload
- **Archive Support**: Upload ZIP and TAR files containing organized document structures
- **Directory Upload**: Select entire directories using browser's webkitdirectory API
- **Structure**: Documents organized as `key/date/files` for systematic categorization
- **Progress Tracking**: Real-time upload progress with file-by-file status reporting
- **Error Handling**: Detailed error messages for failed uploads with retry capability

#### Single Document Upload
- **File Selection**: Support for PDF, HTML, Markdown, and text files
- **Key/Date Input**: Manual classification with custom key and date values
- **Auto-title Generation**: Intelligent title generation from filenames
- **Metadata**: Optional description field for additional context
- **Validation**: File type and size validation before upload

#### Document Organization
- **Key-based Filtering**: Filter documents by organizational keys (e.g., company symbols)
- **Date-based Filtering**: Further filter by dates or time periods
- **Smart Navigation**: 
  - Single document: Auto-opens immediately
  - Multiple documents: Shows selection list
  - No documents: Clear "not found" messaging

### 2. Document Viewing

#### PDF Documents
- **react-pdf Integration**: High-performance PDF rendering with react-pdf-selection
- **Page Navigation**: Smooth scrolling between pages
- **Zoom Support**: Optimized scaling for readability (0.8x default for performance)
- **Text Selection**: Native PDF text selection with coordinate tracking
- **Coordinate System**: Normalized coordinate handling for precise annotation placement

#### HTML Documents
- **Native Rendering**: Direct HTML rendering with full CSS support
- **Text Selection**: DOM-based text selection with character offset calculation
- **Interactive Elements**: Full support for links, images, and other HTML elements
- **Responsive Display**: Adapts to container width while maintaining readability

#### Markdown Documents
- **Rendered Display**: Markdown converted to HTML for rich formatting
- **Text Selection**: Same DOM-based selection as HTML documents
- **Formatting Support**: Headers, lists, code blocks, tables, and inline formatting
- **Character Offset Tracking**: Precise positioning for annotation highlighting

### 3. Annotation System

#### Text Selection
- **Universal Selection**: Works across all document types (PDF, HTML, Markdown, Text)
- **Visual Feedback**: Temporary highlighting during annotation creation
- **Character Offset Calculation**: Precise text positioning for reliable highlighting
- **Range Validation**: Ensures selected text matches stored annotations

#### Annotation Creation
- **Comment Interface**: Rich text input for annotation comments
- **Document Comments**: General comments not tied to specific text selections
- **Author Tracking**: Automatic attribution to authenticated users
- **Timestamp Recording**: Creation and modification timestamps
- **Coordinate Storage**: PDF coordinates or character offsets based on document type

#### Annotation Display
- **Sidebar Interface**: All annotations displayed in organized sidebar
- **Highlighting**: Visual highlighting of annotated text in main document
- **Click Navigation**: Click annotations to scroll to highlighted text
- **Page Information**: Display page numbers for PDF annotations
- **Author Information**: Show annotation author and creation date

#### Annotation Management
- **Delete Functionality**: Remove annotations with immediate UI updates
- **Highlight Cleanup**: Automatic removal of highlighting when annotations are deleted
- **Real-time Updates**: Changes reflected immediately across all interface elements
- **Scroll Prevention**: No unwanted scrolling when deleting annotations

### 4. User Interface

#### Layout and Navigation
- **Three-pane Design**: 
  - Left: Document browser and upload controls
  - Center: Main document viewer
  - Right: Annotation sidebar
- **Responsive Layout**: Adapts to different screen sizes
- **Always-available Controls**: Upload buttons accessible from any page

#### Document Browser
- **Key-Date Selectors**: Dropdown menus for filtering documents
- **Document Cards**: Rich preview cards with metadata
- **Active Document Highlighting**: Current document highlighted in browser
- **Quick Navigation**: One-click access to any document

#### Upload Controls
- **Persistent Access**: Upload buttons always visible in left sidebar
- **Modal Dialogs**: Clean, focused upload interfaces
- **Progress Indicators**: Real-time upload progress and status
- **Success Feedback**: Clear confirmation of successful uploads

### 5. Authentication and Security

#### Google OAuth Integration
- **Secure Login**: Google OAuth 2.0 for user authentication
- **Session Management**: Persistent login sessions with proper token handling
- **User Context**: User information available throughout the application
- **Logout Functionality**: Clean session termination

#### Access Control
- **Document Ownership**: Users can only access their own documents
- **Annotation Ownership**: Users can only delete their own annotations
- **File Security**: Secure file serving with authentication checks
- **Input Validation**: All user inputs validated and sanitized

### 6. Performance Optimizations

#### PDF Rendering
- **Optimized Scale**: 0.8x scaling for improved rendering performance
- **Lazy Loading**: Pages loaded as needed to reduce memory usage
- **Efficient Highlighting**: Minimal DOM manipulation for annotation display
- **Coordinate Caching**: Efficient coordinate system transformations

#### DOM Manipulation
- **Efficient Highlighting**: TreeWalker API for fast text node traversal
- **Cleanup Optimization**: Proper cleanup of DOM modifications
- **Memory Management**: Prevents memory leaks from annotation highlighting
- **Batch Operations**: Efficient batch processing of multiple annotations

#### Network Optimization
- **Blob URLs**: Efficient PDF loading with authentication
- **Progress Tracking**: Upload progress monitoring
- **Error Recovery**: Robust error handling with retry capabilities
- **Auto-refresh**: Smart refreshing of document lists after uploads

### 7. Technical Implementation

#### Frontend Architecture
- **React 18**: Modern React with hooks and functional components
- **TypeScript**: Full type safety throughout the application
- **Material-UI**: Professional component library with theming
- **Context API**: State management for annotations and authentication

#### Backend Architecture
- **FastAPI**: High-performance async Python web framework
- **PostgreSQL**: Robust relational database for data persistence
- **SQLAlchemy**: Async ORM for database operations
- **File Processing**: Multi-format document processing pipeline

#### Integration Points
- **REST API**: Clean API design with OpenAPI documentation
- **Docker Compose**: Containerized development environment
- **Volume Mounting**: Persistent data storage
- **Environment Configuration**: Flexible configuration management

## Upcoming Features

### Enhanced Annotation Features
- **Annotation Threading**: Reply to annotations and create discussion threads
- **Rich Text Comments**: Markdown support in annotation comments
- **Annotation Categories**: Tag and categorize annotations
- **Search and Filter**: Find annotations by content, author, or date

### Collaboration Features
- **Real-time Updates**: WebSocket-based live collaboration
- **User Presence**: See who else is viewing documents
- **Shared Annotations**: Public annotations visible to all users
- **Team Workspaces**: Organized spaces for team collaboration

### Advanced Document Features
- **Document Versioning**: Track changes and versions over time
- **Document Comparison**: Side-by-side comparison of document versions
- **Export Options**: Export annotations to various formats
- **Integration APIs**: Connect with external document management systems

### User Experience Enhancements
- **Dark Mode**: Dark theme option for reduced eye strain
- **Keyboard Shortcuts**: Power user shortcuts for common actions
- **Mobile Optimization**: Enhanced mobile experience
- **Accessibility**: Full WCAG compliance for accessibility