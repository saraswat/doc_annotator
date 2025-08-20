import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Checkbox,
  IconButton,
  Divider,
  Chip,
  Stack,
  Button,
  TextField
} from '@mui/material';
import {
  Task as TaskIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Flag as FlagIcon
} from '@mui/icons-material';
import { ProblemContext, Task } from '../../types/chat';
import { format } from 'date-fns';

interface ContextPanelProps {
  context: ProblemContext | null;
  sessionId?: string;
  onUpdateContext: (context: Partial<ProblemContext>) => void;
}

const ContextPanel: React.FC<ContextPanelProps> = ({
  context,
  sessionId,
  onUpdateContext
}) => {
  const [editMode, setEditMode] = useState(false);
  const [editedSummary, setEditedSummary] = useState(context?.summary || '');
  const [newTask, setNewTask] = useState('');

  const handleTaskToggle = (taskId: string) => {
    if (!context) return;
    
    const updatedTasks = context.tasks.map(task =>
      task.id === taskId
        ? { 
            ...task, 
            status: (task.status === 'completed' ? 'pending' : 'completed') as 'pending' | 'in_progress' | 'completed',
            completedAt: task.status === 'completed' ? undefined : new Date()
          }
        : task
    );
    
    onUpdateContext({ tasks: updatedTasks });
  };

  const handleAddTask = () => {
    if (!newTask.trim() || !context) return;
    
    const task: Task = {
      id: `task-${Date.now()}`,
      description: newTask.trim(),
      status: 'pending',
      priority: 'medium',
      createdAt: new Date()
    };
    
    onUpdateContext({ tasks: [...context.tasks, task] });
    setNewTask('');
  };

  const handleDeleteTask = (taskId: string) => {
    if (!context) return;
    
    const updatedTasks = context.tasks.filter(task => task.id !== taskId);
    onUpdateContext({ tasks: updatedTasks });
  };

  const handleSaveSummary = () => {
    onUpdateContext({ summary: editedSummary });
    setEditMode(false);
  };

  const getPriorityColor = (priority: string): "error" | "warning" | "info" | "default" => {
    switch (priority) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'info';
      default: return 'default';
    }
  };

  if (!context) {
    return (
      <Paper sx={{ height: '100%', p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Problem Context
        </Typography>
        <Typography color="text.secondary">
          No active context. Start a conversation to begin.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Box p={2}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Problem Context</Typography>
          <IconButton size="small" onClick={() => setEditMode(!editMode)}>
            <EditIcon fontSize="small" />
          </IconButton>
        </Stack>
        
        <Typography variant="caption" color="text.secondary">
          Last updated: {format(new Date(context.updatedAt), 'PPp')}
        </Typography>
      </Box>

      <Divider />

      {/* Summary Section */}
      <Box p={2}>
        <Typography variant="subtitle2" gutterBottom>
          Current Goal
        </Typography>
        
        {editMode ? (
          <Box>
            <TextField
              fullWidth
              multiline
              rows={3}
              value={editedSummary}
              onChange={(e) => setEditedSummary(e.target.value)}
              variant="outlined"
              size="small"
            />
            <Stack direction="row" spacing={1} mt={1}>
              <Button size="small" onClick={handleSaveSummary}>
                Save
              </Button>
              <Button 
                size="small" 
                onClick={() => {
                  setEditMode(false);
                  setEditedSummary(context.summary || '');
                }}
              >
                Cancel
              </Button>
            </Stack>
          </Box>
        ) : (
          <Typography variant="body2" paragraph>
            {context.summary || 'No summary yet. The AI will update this as the conversation progresses.'}
          </Typography>
        )}
        
        {context.currentGoal && (
          <Chip 
            label={context.currentGoal} 
            size="small" 
            color="primary" 
            variant="outlined"
          />
        )}
      </Box>

      <Divider />

      {/* Tasks Section */}
      <Box flex={1} overflow="auto" p={2}>
        <Typography variant="subtitle2" gutterBottom>
          Tasks & Action Items
        </Typography>
        
        <List dense>
          {context.tasks.map((task) => (
            <ListItem
              key={task.id}
              secondaryAction={
                <IconButton 
                  edge="end" 
                  size="small"
                  onClick={() => handleDeleteTask(task.id)}
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              }
            >
              <ListItemIcon>
                <Checkbox
                  edge="start"
                  checked={task.status === 'completed'}
                  onChange={() => handleTaskToggle(task.id)}
                />
              </ListItemIcon>
              <ListItemText
                primary={
                  <Typography
                    variant="body2"
                    sx={{
                      textDecoration: task.status === 'completed' ? 'line-through' : 'none'
                    }}
                  >
                    {task.description}
                  </Typography>
                }
                secondary={
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <Chip
                      label={task.priority}
                      size="small"
                      color={getPriorityColor(task.priority)}
                      sx={{ height: 16, fontSize: '0.7rem' }}
                    />
                    {task.completedAt && (
                      <Typography variant="caption" color="text.secondary">
                        Completed {format(new Date(task.completedAt), 'MMM d')}
                      </Typography>
                    )}
                  </Stack>
                }
              />
            </ListItem>
          ))}
        </List>
        
        {/* Add Task */}
        <Box mt={1}>
          <Stack direction="row" spacing={1}>
            <TextField
              size="small"
              fullWidth
              placeholder="Add a task..."
              value={newTask}
              onChange={(e) => setNewTask(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddTask();
                }
              }}
            />
            <IconButton size="small" onClick={handleAddTask}>
              <AddIcon />
            </IconButton>
          </Stack>
        </Box>
      </Box>

      {/* Related Documents */}
      {context.relevantDocuments && context.relevantDocuments.length > 0 && (
        <>
          <Divider />
          <Box p={2}>
            <Typography variant="subtitle2" gutterBottom>
              Related Documents
            </Typography>
            <Stack direction="row" spacing={0.5} flexWrap="wrap">
              {context.relevantDocuments.map(docId => (
                <Chip 
                  key={docId}
                  label={docId} 
                  size="small" 
                  variant="outlined"
                />
              ))}
            </Stack>
          </Box>
        </>
      )}
    </Paper>
  );
};

export default ContextPanel;