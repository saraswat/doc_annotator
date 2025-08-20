import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  TextField,
  IconButton,
  Button,
  Tooltip,
  Chip,
  Stack,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  Popover,
  Typography
} from '@mui/material';
import {
  Send as SendIcon,
  Settings as SettingsIcon,
  Add as AddIcon,
  Search as SearchIcon,
  Science as ResearchIcon,
  Language as WebIcon
} from '@mui/icons-material';
import { ChatSettings } from '../../types/chat';
import chatService from '../../services/chatService';

interface ChatInputProps {
  onSend: (message: string, attachments?: any[]) => void;
  disabled?: boolean;
  settings: ChatSettings;
  onSettingsChange: (settings: Partial<ChatSettings>) => void;
  onAddDocument?: (documentId: string) => void;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  disabled,
  settings,
  onSettingsChange,
  onAddDocument
}) => {
  const [message, setMessage] = useState('');
  const [settingsAnchor, setSettingsAnchor] = useState<null | HTMLElement>(null);
  const [availableModels, setAvailableModels] = useState<Array<{value: string, label: string}>>([]);
  const textFieldRef = useRef<HTMLDivElement>(null);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Load available models from API
  useEffect(() => {
    const loadModels = async () => {
      try {
        const modelsData = await chatService.getAvailableModels();
        const modelOptions = modelsData.models.map(model => ({
          value: model.id,
          label: model.common_name
        }));
        setAvailableModels(modelOptions);
        
        // Set default model if current model is not in the list
        if (!modelsData.models.find(m => m.id === settings.model)) {
          onSettingsChange({ model: modelsData.default_model });
        }
      } catch (error) {
        console.error('Failed to load available models:', error);
        // Fallback to empty list - user can still type model name
        setAvailableModels([]);
      }
    };
    
    loadModels();
  }, [settings.model, onSettingsChange]);

  return (
    <Box>
      {/* Active Settings Display */}
      <Stack direction="row" spacing={1} sx={{ mb: 1 }} flexWrap="wrap">
        <Chip 
          label={`Model: ${settings.model}`} 
          size="small" 
          variant="outlined"
        />
        {settings.webBrowsing && (
          <Chip 
            icon={<WebIcon />} 
            label="Web Browsing" 
            size="small" 
            disabled={true}
            sx={{
              opacity: 0.5,
              '& .MuiChip-deleteIcon': {
                display: 'none'
              }
            }}
          />
        )}
        {settings.deepResearch && (
          <Chip 
            icon={<ResearchIcon />} 
            label="Deep Research" 
            size="small" 
            disabled={true}
            sx={{
              opacity: 0.5,
              '& .MuiChip-deleteIcon': {
                display: 'none'
              }
            }}
          />
        )}
        {settings.includeDocuments.length > 0 && (
          <Chip 
            label={`${settings.includeDocuments.length} Documents`} 
            size="small" 
            color="success"
          />
        )}
      </Stack>

      {/* Input Field with Controls */}
      <Box display="flex" alignItems="flex-end" gap={1}>
        <TextField
          ref={textFieldRef}
          fullWidth
          multiline
          maxRows={6}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message... (Shift+Enter for new line)"
          disabled={disabled}
          variant="outlined"
          sx={{
            '& .MuiOutlinedInput-root': {
              borderRadius: 2
            }
          }}
        />

        {/* Control Buttons */}
        <Stack direction="row" spacing={0.5}>
          {/* Add Document */}
          {onAddDocument && (
            <Tooltip title="Add Documents">
              <IconButton 
                color="primary"
                onClick={() => {
                  // For now, just add a placeholder document
                  onAddDocument('sample-doc');
                }}
              >
                <AddIcon />
              </IconButton>
            </Tooltip>
          )}

          {/* Web Browsing Toggle - Disabled/Greyed Out */}
          <Tooltip title="Web Browsing (Coming Soon)">
            <span>
              <IconButton 
                disabled={true}
                sx={{
                  color: 'rgba(0, 0, 0, 0.26)',
                  cursor: 'not-allowed'
                }}
              >
                <WebIcon />
              </IconButton>
            </span>
          </Tooltip>

          {/* Deep Research Toggle - Disabled/Greyed Out */}
          <Tooltip title="Deep Research (Coming Soon)">
            <span>
              <IconButton 
                disabled={true}
                sx={{
                  color: 'rgba(0, 0, 0, 0.26)',
                  cursor: 'not-allowed'
                }}
              >
                <ResearchIcon />
              </IconButton>
            </span>
          </Tooltip>

          {/* Settings */}
          <Tooltip title="Chat Settings">
            <IconButton onClick={(e) => setSettingsAnchor(e.currentTarget)}>
              <SettingsIcon />
            </IconButton>
          </Tooltip>

          {/* Send Button */}
          <Tooltip title="Send Message">
            <IconButton 
              color="primary" 
              onClick={handleSend}
              disabled={disabled || !message.trim()}
              sx={{
                backgroundColor: 'primary.main',
                color: 'white',
                '&:hover': {
                  backgroundColor: 'primary.dark'
                },
                '&:disabled': {
                  backgroundColor: 'grey.300',
                  color: 'grey.500'
                }
              }}
            >
              <SendIcon />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Settings Menu */}
      <Popover
        open={Boolean(settingsAnchor)}
        anchorEl={settingsAnchor}
        onClose={() => setSettingsAnchor(null)}
        anchorOrigin={{
          vertical: 'top',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'bottom',
          horizontal: 'right',
        }}
      >
        <Box p={2} minWidth={300}>
          <Stack spacing={2}>
            <Typography variant="h6">Chat Settings</Typography>
            
            <Box>
              <Typography variant="body2" gutterBottom>Model:</Typography>
              <Select
                fullWidth
                size="small"
                value={settings.model}
                onChange={(e) => onSettingsChange({ model: e.target.value })}
              >
                {availableModels.map(model => (
                  <MenuItem key={model.value} value={model.value}>
                    {model.label}
                  </MenuItem>
                ))}
              </Select>
            </Box>
            
            <Box>
              <Typography variant="body2" gutterBottom>
                Temperature: {settings.temperature}
              </Typography>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={settings.temperature}
                onChange={(e) => onSettingsChange({ 
                  temperature: parseFloat(e.target.value) 
                })}
                style={{ width: '100%' }}
              />
            </Box>

            <Box>
              <Typography variant="body2" gutterBottom>Max Tokens:</Typography>
              <TextField
                type="number"
                size="small"
                fullWidth
                value={settings.maxTokens}
                onChange={(e) => onSettingsChange({ 
                  maxTokens: parseInt(e.target.value) || 2000
                })}
              />
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={settings.webBrowsing}
                  disabled={true}
                  onChange={(e) => onSettingsChange({ webBrowsing: e.target.checked })}
                />
              }
              label="Web Browsing (Coming Soon)"
              sx={{ opacity: 0.5 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.deepResearch}
                  disabled={true}
                  onChange={(e) => onSettingsChange({ deepResearch: e.target.checked })}
                />
              }
              label="Deep Research Mode (Coming Soon)"
              sx={{ opacity: 0.5 }}
            />
          </Stack>
        </Box>
      </Popover>
    </Box>
  );
};

export default ChatInput;