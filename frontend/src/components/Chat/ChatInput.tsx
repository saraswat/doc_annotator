import React, { useState, useRef } from 'react';
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

  const availableModels = [
    { value: 'gpt-4', label: 'GPT-4' },
    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { value: 'claude-3-opus', label: 'Claude 3 Opus' },
    { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
    { value: 'custom', label: 'Custom Endpoint' }
  ];

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
            color="primary"
            onDelete={() => onSettingsChange({ webBrowsing: false })}
          />
        )}
        {settings.deepResearch && (
          <Chip 
            icon={<ResearchIcon />} 
            label="Deep Research" 
            size="small" 
            color="secondary"
            onDelete={() => onSettingsChange({ deepResearch: false })}
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

          {/* Web Browsing Toggle */}
          <Tooltip title="Toggle Web Browsing">
            <IconButton 
              color={settings.webBrowsing ? "primary" : "default"}
              onClick={() => onSettingsChange({ 
                webBrowsing: !settings.webBrowsing 
              })}
            >
              <WebIcon />
            </IconButton>
          </Tooltip>

          {/* Deep Research Toggle */}
          <Tooltip title="Toggle Deep Research">
            <IconButton 
              color={settings.deepResearch ? "secondary" : "default"}
              onClick={() => onSettingsChange({ 
                deepResearch: !settings.deepResearch 
              })}
            >
              <ResearchIcon />
            </IconButton>
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
                  onChange={(e) => onSettingsChange({ webBrowsing: e.target.checked })}
                />
              }
              label="Web Browsing"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={settings.deepResearch}
                  onChange={(e) => onSettingsChange({ deepResearch: e.target.checked })}
                />
              }
              label="Deep Research Mode"
            />
          </Stack>
        </Box>
      </Popover>
    </Box>
  );
};

export default ChatInput;