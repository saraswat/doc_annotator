import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  IconButton,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Chat as ChatIcon
} from '@mui/icons-material';
import { ChatSession } from '../../types/chat';
import { useChat } from '../../hooks/useChat';
import { useViewContext } from '../../contexts/ViewContext';
import { format } from 'date-fns';

const ChatSessionList: React.FC = () => {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [newSessionDialog, setNewSessionDialog] = useState(false);
  const [newSessionTitle, setNewSessionTitle] = useState('');
  const { loadSessions, createSession, deleteSession } = useChat();
  const { viewState, setCurrentChatSession } = useViewContext();

  useEffect(() => {
    const loadData = async () => {
      try {
        await loadSessions();
        // For now, we'll manage sessions locally
        // In a full implementation, sessions would come from the hook
      } catch (error) {
        console.error('Failed to load chat sessions:', error);
      }
    };
    loadData();
  }, [loadSessions]);

  const handleCreateSession = async () => {
    try {
      const session = await createSession(newSessionTitle || undefined);
      setSessions(prev => [session, ...prev]);
      setCurrentChatSession(session.id);
      setNewSessionDialog(false);
      setNewSessionTitle('');
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleDeleteSession = async (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (window.confirm('Are you sure you want to delete this chat session?')) {
      try {
        await deleteSession(sessionId);
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        if (viewState.currentChatSessionId === sessionId) {
          setCurrentChatSession(undefined);
        }
      } catch (error) {
        console.error('Failed to delete session:', error);
      }
    }
  };

  const handleSelectSession = (sessionId: string) => {
    setCurrentChatSession(sessionId);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" component="div" sx={{ display: 'flex', alignItems: 'center' }}>
          <ChatIcon sx={{ mr: 1 }} />
          Chat Sessions
        </Typography>
        <IconButton 
          size="small" 
          onClick={() => setNewSessionDialog(true)}
          color="primary"
        >
          <AddIcon />
        </IconButton>
      </Box>

      <List dense>
        {sessions.map((session) => (
          <ListItem 
            key={session.id} 
            disablePadding
            secondaryAction={
              <IconButton 
                edge="end" 
                size="small"
                onClick={(e) => handleDeleteSession(session.id, e)}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            }
          >
            <ListItemButton 
              selected={viewState.currentChatSessionId === session.id}
              onClick={() => handleSelectSession(session.id)}
            >
              <ListItemText
                primary={session.title}
                secondary={`${session.messageCount} messages • ${format(new Date(session.updatedAt), 'MMM d')}`}
                primaryTypographyProps={{ 
                  noWrap: true,
                  fontSize: '0.9rem'
                }}
                secondaryTypographyProps={{ 
                  fontSize: '0.75rem'
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}

        {sessions.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 3, color: 'text.secondary' }}>
            <Typography variant="body2">
              No chat sessions yet
            </Typography>
            <Button 
              variant="outlined" 
              size="small" 
              onClick={() => setNewSessionDialog(true)}
              sx={{ mt: 1 }}
            >
              Start New Chat
            </Button>
          </Box>
        )}
      </List>

      {/* New Session Dialog */}
      <Dialog 
        open={newSessionDialog} 
        onClose={() => setNewSessionDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>New Chat Session</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            label="Session Title (optional)"
            fullWidth
            variant="outlined"
            value={newSessionTitle}
            onChange={(e) => setNewSessionTitle(e.target.value)}
            placeholder="e.g., Document Analysis, Research Questions"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setNewSessionDialog(false)}>
            Cancel
          </Button>
          <Button onClick={handleCreateSession} variant="contained">
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ChatSessionList;