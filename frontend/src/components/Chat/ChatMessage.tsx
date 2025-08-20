import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Chip,
  Stack,
  Fade,
  Tooltip,
  Snackbar
} from '@mui/material';
import {
  Person as UserIcon,
  SmartToy as BotIcon,
  Refresh as RetryIcon,
  Error as ErrorIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  ContentCopy as CopyIcon
} from '@mui/icons-material';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { format } from 'date-fns';
import chatService from '../../services/chatService';

interface ChatMessageProps {
  message: ChatMessageType;
  messageOrder?: number; // Position of LLM response in session (for feedback)
  onRetry?: () => void;
  onFeedbackChange?: () => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, messageOrder, onRetry, onFeedbackChange }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isAssistant = message.role === 'assistant';
  const isError = message.status === 'error';
  const isSending = message.status === 'sending';
  
  const [feedback, setFeedback] = useState(message.feedback);
  const [copySuccess, setCopySuccess] = useState(false);

  const handleThumbsUp = async () => {
    if (!isAssistant || !messageOrder) return;
    
    try {
      const newFeedback = await chatService.submitFeedback(message.id, 'thumbs_up', messageOrder);
      setFeedback(newFeedback);
      if (onFeedbackChange) onFeedbackChange();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleThumbsDown = async () => {
    if (!isAssistant || !messageOrder) return;
    
    try {
      const newFeedback = await chatService.submitFeedback(message.id, 'thumbs_down', messageOrder);
      setFeedback(newFeedback);
      if (onFeedbackChange) onFeedbackChange();
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  return (
    <>
      <Fade in={true} timeout={300}>
        <Box
          sx={{
            py: 3,
            px: { xs: 2, sm: 4, md: 6 },
            maxWidth: '100%',
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
          }}
        >
          <Box
            sx={{
              maxWidth: isUser ? '80%' : '100%',
              borderLeft: isUser ? 'none' : `3px solid ${isSystem ? '#9e9e9e' : '#1976d2'}`,
              borderRight: isUser ? '3px solid #1976d2' : 'none',
              backgroundColor: isUser 
                ? 'rgba(25, 118, 210, 0.02)' 
                : isError 
                ? 'rgba(244, 67, 54, 0.02)'
                : isSystem
                ? 'rgba(158, 158, 158, 0.02)'
                : 'rgba(76, 175, 80, 0.02)',
              transition: 'background-color 0.2s ease',
              py: 2,
              px: 3,
              borderRadius: 1,
              '&:hover': {
                backgroundColor: isUser 
                  ? 'rgba(25, 118, 210, 0.04)' 
                  : isError 
                  ? 'rgba(244, 67, 54, 0.04)'
                  : isSystem
                  ? 'rgba(158, 158, 158, 0.04)'
                  : 'rgba(76, 175, 80, 0.04)',
              }
            }}
          >
          {/* Message Header */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5, flexDirection: isUser ? 'row-reverse' : 'row' }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                mr: isUser ? 0 : 2,
                ml: isUser ? 2 : 0
              }}
            >
              {isUser ? (
                <UserIcon sx={{ fontSize: 20, color: 'text.secondary', mr: isUser ? 0 : 1, ml: isUser ? 1 : 0 }} />
              ) : (
                <BotIcon sx={{ fontSize: 20, color: isSystem ? 'text.secondary' : 'primary.main', mr: isUser ? 0 : 1, ml: isUser ? 1 : 0 }} />
              )}
              <Typography
                variant="subtitle2"
                sx={{
                  fontWeight: 600,
                  color: isUser ? 'text.primary' : isSystem ? 'text.secondary' : 'primary.main',
                  fontSize: '0.875rem',
                  mr: isUser ? 1 : 0,
                  ml: isUser ? 0 : 1
                }}
              >
                {isUser ? 'You' : isSystem ? 'System' : 'Assistant'}
              </Typography>
            </Box>

            <Typography variant="caption" color="text.secondary" sx={{ ml: isUser ? 0 : 'auto', mr: isUser ? 'auto' : 0 }}>
              {format(new Date(message.timestamp), 'HH:mm')}
            </Typography>
          </Box>

          {/* Message Content */}
          <Box sx={{ pl: isUser ? 0 : 4, pr: isUser ? 4 : 0 }}>
          <Typography
            variant="body1"
            sx={{
              lineHeight: 1.6,
              fontSize: '0.95rem',
              color: 'text.primary',
              opacity: isSending ? 0.6 : 1,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
              '& code': {
                backgroundColor: 'rgba(0,0,0,0.08)',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '0.875rem',
                fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", monospace',
                border: '1px solid rgba(0,0,0,0.12)'
              },
              '& pre': {
                backgroundColor: 'rgba(0,0,0,0.04)',
                padding: '12px 16px',
                borderRadius: '8px',
                overflowX: 'auto',
                fontSize: '0.875rem',
                fontFamily: '"Monaco", "Menlo", "Ubuntu Mono", monospace',
                border: '1px solid rgba(0,0,0,0.08)',
                margin: '8px 0'
              }
            }}
            dangerouslySetInnerHTML={{ __html: message.content }}
          />

          {/* Document References */}
          {message.metadata?.documentReferences && message.metadata.documentReferences.length > 0 && (
            <Stack direction="row" spacing={0.5} sx={{ mt: 2 }} flexWrap="wrap">
              {message.metadata.documentReferences.map((ref, index) => (
                <Chip
                  key={index}
                  label={ref.documentName}
                  size="small"
                  variant="outlined"
                  sx={{
                    height: 24,
                    fontSize: '0.75rem',
                    backgroundColor: 'rgba(25, 118, 210, 0.08)',
                    borderColor: 'rgba(25, 118, 210, 0.2)',
                    color: 'primary.main'
                  }}
                />
              ))}
            </Stack>
          )}

          {/* Metadata */}
          {(message.metadata?.model || message.metadata?.tokens) && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 1.5, gap: 2 }}>
              {message.metadata?.model && (
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {message.metadata.model}
                </Typography>
              )}
              {message.metadata?.tokens && (
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                  {message.metadata.tokens} tokens
                </Typography>
              )}
            </Box>
          )}

          {/* Error handling */}
          {isError && (
            <Box 
              sx={{ 
                mt: 2, 
                display: 'flex', 
                alignItems: 'center',
                p: 1.5,
                borderRadius: 1,
                backgroundColor: 'error.light',
                color: 'error.contrastText'
              }}
            >
              <ErrorIcon fontSize="small" sx={{ mr: 1 }} />
              <Typography variant="body2" sx={{ mr: 2, flex: 1 }}>
                Failed to send message
              </Typography>
              {onRetry && (
                <IconButton 
                  size="small" 
                  onClick={onRetry}
                  sx={{ 
                    color: 'error.contrastText',
                    '&:hover': { backgroundColor: 'rgba(255,255,255,0.1)' }
                  }}
                >
                  <RetryIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
          )}

          {/* Action buttons for assistant messages */}
          {isAssistant && !isSending && (
            <Box sx={{ 
              mt: 2, 
              display: 'flex', 
              alignItems: 'center', 
              gap: 0.5,
              justifyContent: isUser ? 'flex-end' : 'flex-start'
            }}>
              <Tooltip title="Copy message">
                <IconButton
                  size="small"
                  onClick={handleCopy}
                  sx={{
                    opacity: 0.6,
                    '&:hover': { opacity: 1 }
                  }}
                >
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Helpful">
                <IconButton
                  size="small"
                  onClick={handleThumbsUp}
                  sx={{
                    opacity: feedback?.feedbackType === 'thumbs_up' ? 1 : 0.6,
                    color: feedback?.feedbackType === 'thumbs_up' ? 'success.main' : 'text.secondary',
                    '&:hover': { 
                      opacity: 1,
                      color: 'success.main'
                    }
                  }}
                >
                  <ThumbUpIcon fontSize="small" />
                </IconButton>
              </Tooltip>

              <Tooltip title="Not helpful">
                <IconButton
                  size="small"
                  onClick={handleThumbsDown}
                  sx={{
                    opacity: feedback?.feedbackType === 'thumbs_down' ? 1 : 0.6,
                    color: feedback?.feedbackType === 'thumbs_down' ? 'error.main' : 'text.secondary',
                    '&:hover': { 
                      opacity: 1,
                      color: 'error.main'
                    }
                  }}
                >
                  <ThumbDownIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}

          {/* Sending indicator */}
          {isSending && (
            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
              <Box
                sx={{
                  display: 'inline-flex',
                  '& > div': {
                    width: 6,
                    height: 6,
                    borderRadius: '50%',
                    backgroundColor: 'text.secondary',
                    animation: 'typing 1.4s infinite ease-in-out',
                    '&:nth-of-type(1)': { animationDelay: '-0.32s' },
                    '&:nth-of-type(2)': { animationDelay: '-0.16s', ml: 0.5 },
                    '&:nth-of-type(3)': { ml: 0.5 }
                  },
                  '@keyframes typing': {
                    '0%, 80%, 100%': { opacity: 0.3 },
                    '40%': { opacity: 1 }
                  }
                }}
              >
                <div></div>
                <div></div>
                <div></div>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                {isUser ? 'Sending...' : 'Thinking...'}
              </Typography>
            </Box>
          )}
            </Box>
          </Box>
        </Box>
      </Fade>
      
      {/* Copy success notification */}
      <Snackbar
        open={copySuccess}
        autoHideDuration={2000}
        onClose={() => setCopySuccess(false)}
        message="Copied to clipboard"
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      />
    </>
  );
};

export default ChatMessage;