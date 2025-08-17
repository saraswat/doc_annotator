import socketio
from typing import Dict, Set
import json
from app.core.security import validate_token

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*"
)

# Create Socket.IO ASGI app
sio_app = socketio.ASGIApp(sio)

class ConnectionManager:
    def __init__(self):
        # Track active connections by document ID
        self.document_connections: Dict[int, Set[str]] = {}
        # Track user sessions
        self.user_sessions: Dict[str, str] = {}
    
    async def connect(self, sid: str, user_id: str):
        """Handle new WebSocket connection."""
        self.user_sessions[sid] = user_id
        await sio.emit('connected', {'message': 'Connected to annotation service'}, to=sid)
    
    async def disconnect(self, sid: str):
        """Handle WebSocket disconnection."""
        # Remove from all document rooms
        for doc_id, connections in self.document_connections.items():
            if sid in connections:
                connections.remove(sid)
        
        # Remove user session
        if sid in self.user_sessions:
            del self.user_sessions[sid]
    
    async def join_document(self, sid: str, document_id: int):
        """Join a document room for real-time updates."""
        if document_id not in self.document_connections:
            self.document_connections[document_id] = set()
        
        self.document_connections[document_id].add(sid)
        await sio.enter_room(sid, f"document_{document_id}")
        
        # Notify others in the document
        await self.broadcast_to_document(
            document_id,
            {
                "type": "user_joined",
                "userId": self.user_sessions.get(sid)
            },
            exclude_sid=sid
        )
    
    async def leave_document(self, sid: str, document_id: int):
        """Leave a document room."""
        if document_id in self.document_connections:
            self.document_connections[document_id].discard(sid)
        
        await sio.leave_room(sid, f"document_{document_id}")
        
        # Notify others
        await self.broadcast_to_document(
            document_id,
            {
                "type": "user_left",
                "userId": self.user_sessions.get(sid)
            }
        )
    
    async def broadcast_to_document(
        self, 
        document_id: int, 
        data: dict, 
        exclude_sid: str = None
    ):
        """Broadcast a message to all users viewing a document."""
        room = f"document_{document_id}"
        await sio.emit(
            'annotation_update',
            data,
            room=room,
            skip_sid=exclude_sid
        )
    
    async def send_to_user(self, user_id: str, event: str, data: dict):
        """Send a message to a specific user."""
        for sid, uid in self.user_sessions.items():
            if uid == user_id:
                await sio.emit(event, data, to=sid)

# Create global manager instance
manager = ConnectionManager()

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle client connection."""
    if auth and 'token' in auth:
        # Validate token and get user ID
        user_id = validate_token(auth['token'])
        if user_id:
            await manager.connect(sid, user_id)
            return True
    return False

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    await manager.disconnect(sid)

@sio.event
async def join_document(sid, data):
    """Handle joining a document room."""
    document_id = data.get('documentId')
    if document_id:
        await manager.join_document(sid, document_id)

@sio.event
async def leave_document(sid, data):
    """Handle leaving a document room."""
    document_id = data.get('documentId')
    if document_id:
        await manager.leave_document(sid, document_id)

@sio.event
async def cursor_position(sid, data):
    """Share cursor position for collaborative features."""
    document_id = data.get('documentId')
    position = data.get('position')
    
    if document_id:
        await manager.broadcast_to_document(
            document_id,
            {
                "type": "cursor_update",
                "userId": manager.user_sessions.get(sid),
                "position": position
            },
            exclude_sid=sid
        )