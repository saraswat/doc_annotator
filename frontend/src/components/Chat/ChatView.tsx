import React, { useState, useEffect, useRef } from 'react';
import { Box, Paper, Divider, CircularProgress, Typography } from '@mui/material';
import { useChat } from '../../hooks/useChat';
import { useContext } from '../../hooks/useContext';
import ChatMessage from './ChatMessage';
import { ChatSession, ChatMessage as ChatMessageType, ChatSettings } from '../../types/chat';
import chatService from '../../services/chatService';

interface ChatViewProps {
  sessionId?: string;
  onNewSession?: () => void;
}

const ChatView: React.FC<ChatViewProps> = ({ sessionId, onNewSession }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [chatSettings] = useState<ChatSettings>({
    model: 'gpt-4',
    temperature: 0.7,
    maxTokens: 2000,
    webBrowsing: false,
    deepResearch: false,
    includeDocuments: []
  });

  const { 
    createSession,
    loadSession,
  } = useChat();
  
  const { 
    context, 
    extractTasksFromMessage 
  } = useContext();

  // Load or create session
  useEffect(() => {
    const initializeSession = async () => {
      if (sessionId) {
        try {
          const session = await loadSession(sessionId);
          setCurrentSession(session);
          // Assume messages come with session
          setMessages((session as any).messages || []);
        } catch (error) {
          console.error('Failed to load session:', error);
        }
      } else {
        try {
          const newSession = await createSession();
          setCurrentSession(newSession);
          setMessages([]);
          if (onNewSession) onNewSession();
        } catch (error) {
          console.error('Failed to create session:', error);
        }
      }
    };
    
    initializeSession();
  }, [sessionId, loadSession, createSession, onNewSession]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (content: string) => {
    if (!currentSession || !content.trim()) return;

    // Add user message immediately
    const userMessage: ChatMessageType = {
      id: `temp-${Date.now()}`,
      sessionId: currentSession.id,
      role: 'user',
      content,
      timestamp: new Date(),
      status: 'sending'
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setInputValue('');

    try {
      // Send message with current settings and context
      const messageData = {
        content,
        settings: chatSettings,
        context_options: {
          problemContext: context,
          documentIds: chatSettings.includeDocuments,
          enableWebBrowsing: chatSettings.webBrowsing,
          enableDeepResearch: chatSettings.deepResearch
        }
      };

      const stream = await chatService.sendMessage(currentSession.id, messageData);

      // Handle streaming response
      const assistantMessage: ChatMessageType = {
        id: `assistant-${Date.now()}`,
        sessionId: currentSession.id,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        status: 'sending'
      };
      
      setMessages(prev => [...prev.slice(0, -1), 
        { ...userMessage, status: 'sent' },
        assistantMessage
      ]);

      let fullResponse = '';

      // Stream the response
      for await (const chunk of chatService.streamResponse(stream)) {
        if (chunk.type === 'chunk' && chunk.content) {
          fullResponse += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.role === 'assistant') {
              lastMessage.content = fullResponse;
            }
            return newMessages;
          });
        } else if (chunk.type === 'complete') {
          // Mark message as sent
          setMessages(prev => {
            const newMessages = [...prev];
            const lastMessage = newMessages[newMessages.length - 1];
            if (lastMessage.role === 'assistant') {
              lastMessage.status = 'sent';
              if (chunk.messageId) {
                lastMessage.id = chunk.messageId;
              }
            }
            return newMessages;
          });
          break;
        } else if (chunk.type === 'error') {
          throw new Error(chunk.error || 'Stream error');
        }
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, {
        id: `error-${Date.now()}`,
        sessionId: currentSession.id,
        role: 'system',
        content: 'Failed to send message. Please try again.',
        timestamp: new Date(),
        status: 'error'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  if (!currentSession) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading chat session...</Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" height="100vh">
      {/* Main Chat Area */}
      <Box flex={1} display="flex" flexDirection="column">
        {/* Messages Area */}
        <Paper 
          elevation={0} 
          sx={{ 
            flex: 1, 
            overflow: 'auto', 
            p: 3,
            backgroundColor: '#f5f5f5'
          }}
        >
          {messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message}
              onRetry={() => handleSendMessage(message.content)}
            />
          ))}
          {isLoading && (
            <Box display="flex" justifyContent="center" p={2}>
              <CircularProgress size={24} />
            </Box>
          )}
          <div ref={messagesEndRef} />
        </Paper>

        <Divider />

        {/* Simple Input Area for now */}
        <Box p={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <input
              style={{
                flex: 1,
                padding: '12px',
                border: '1px solid #ccc',
                borderRadius: '8px',
                outline: 'none'
              }}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
              disabled={isLoading}
            />
            <button
              onClick={() => handleSendMessage(inputValue)}
              disabled={isLoading || !inputValue.trim()}
              style={{
                padding: '12px 24px',
                backgroundColor: '#1976d2',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                opacity: isLoading || !inputValue.trim() ? 0.5 : 1
              }}
            >
              Send
            </button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatView;