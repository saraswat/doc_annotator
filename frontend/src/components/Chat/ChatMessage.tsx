import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  IconButton,
  Chip,
  Stack
} from '@mui/material';
import {
  Person as UserIcon,
  SmartToy as BotIcon,
  Refresh as RetryIcon,
  Error as ErrorIcon
} from '@mui/icons-material';
import { ChatMessage as ChatMessageType } from '../../types/chat';
import { format } from 'date-fns';

interface ChatMessageProps {
  message: ChatMessageType;
  onRetry?: () => void;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message, onRetry }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';
  const isError = message.status === 'error';
  const isSending = message.status === 'sending';

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        alignItems: 'flex-start'
      }}
    >
      {!isUser && (
        <Avatar
          sx={{
            mr: 1,
            bgcolor: isSystem ? 'grey.400' : 'primary.main',
            width: 32,
            height: 32
          }}
        >
          {isSystem ? '!' : <BotIcon fontSize="small" />}
        </Avatar>
      )}

      <Box
        sx={{
          maxWidth: '70%',
          minWidth: '20%'
        }}
      >
        <Paper
          elevation={1}
          sx={{
            p: 2,
            backgroundColor: isUser
              ? 'primary.main'
              : isError
              ? 'error.light'
              : isSystem
              ? 'grey.100'
              : 'white',
            color: isUser ? 'primary.contrastText' : 'text.primary',
            opacity: isSending ? 0.7 : 1
          }}
        >
          <Typography
            variant="body1"
            sx={{
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              '& code': {
                backgroundColor: 'rgba(0,0,0,0.1)',
                padding: '2px 4px',
                borderRadius: 1,
                fontSize: '0.9em'
              }
            }}
            dangerouslySetInnerHTML={{ __html: message.content }}
          />

          {/* Document References */}
          {message.metadata?.documentReferences && (
            <Stack direction="row" spacing={0.5} sx={{ mt: 1 }} flexWrap="wrap">
              {message.metadata.documentReferences.map((ref, index) => (
                <Chip
                  key={index}
                  label={ref.documentName}
                  size="small"
                  variant="outlined"
                  sx={{
                    height: 20,
                    fontSize: '0.7rem',
                    bgcolor: 'rgba(255,255,255,0.1)'
                  }}
                />
              ))}
            </Stack>
          )}

          {/* Error handling */}
          {isError && onRetry && (
            <Box sx={{ mt: 1, display: 'flex', alignItems: 'center' }}>
              <ErrorIcon fontSize="small" sx={{ mr: 0.5 }} />
              <Typography variant="caption" sx={{ mr: 1 }}>
                Failed to send
              </Typography>
              <IconButton size="small" onClick={onRetry}>
                <RetryIcon fontSize="small" />
              </IconButton>
            </Box>
          )}
        </Paper>

        {/* Message metadata */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: isUser ? 'flex-end' : 'flex-start',
            alignItems: 'center',
            mt: 0.5,
            px: 1
          }}
        >
          <Typography variant="caption" color="text.secondary">
            {format(new Date(message.timestamp), 'HH:mm')}
          </Typography>

          {message.metadata?.model && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ mx: 1 }}>
                •
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {message.metadata.model}
              </Typography>
            </>
          )}

          {message.metadata?.tokens && (
            <>
              <Typography variant="caption" color="text.secondary" sx={{ mx: 1 }}>
                •
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {message.metadata.tokens} tokens
              </Typography>
            </>
          )}
        </Box>
      </Box>

      {isUser && (
        <Avatar
          sx={{
            ml: 1,
            bgcolor: 'grey.300',
            width: 32,
            height: 32
          }}
        >
          <UserIcon fontSize="small" />
        </Avatar>
      )}
    </Box>
  );
};

export default ChatMessage;