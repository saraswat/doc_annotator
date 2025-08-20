import React, { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router-dom';
import { Box, Paper, Divider, CircularProgress, Typography } from '@mui/material';
import { SmartToy as BotIcon } from '@mui/icons-material';
import { useChat } from '../../hooks/useChat';
import { useContext } from '../../hooks/useContext';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ContextPanel from './ContextPanel';
import { ChatSession, ChatMessage as ChatMessageType, ChatSettings } from '../../types/chat';
import chatService from '../../services/chatService';

interface ChatViewProps {
  sessionId?: string;
  onNewSession?: () => void;
}

const ChatView: React.FC<ChatViewProps> = ({ sessionId: propSessionId, onNewSession }) => {
  const { sessionId: routeSessionId } = useParams<{ sessionId: string }>();
  const sessionId = propSessionId || routeSessionId;
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatSettings, setChatSettings] = useState<ChatSettings>({
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
    updateContext,
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

    try {
      // Send message with current settings and context
      const messageData = {
        content,
        settings: chatSettings,
        context_options: {
          problemContext: context || undefined,
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

  const handleSettingsChange = (newSettings: Partial<ChatSettings>) => {
    setChatSettings(prev => ({ ...prev, ...newSettings }));
  };

  const handleAddDocument = (documentId: string) => {
    setChatSettings(prev => ({
      ...prev,
      includeDocuments: [...prev.includeDocuments, documentId]
    }));
  };

  if (!currentSession) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
        <Typography sx={{ ml: 2 }}>Loading chat session...</Typography>
      </Box>
    );
  }

  return (
    <Box display="flex" height="100%" sx={{ overflow: 'hidden' }}>
      {/* Main Chat Area */}
      <Box flex={1} display="flex" flexDirection="column">
        {/* Messages Area */}
        <Box 
          sx={{ 
            flex: 1, 
            overflow: 'auto',
            backgroundColor: '#ffffff',
            borderRadius: 0,
            scrollBehavior: 'smooth',
            '&::-webkit-scrollbar': {
              width: '8px',
            },
            '&::-webkit-scrollbar-track': {
              backgroundColor: 'rgba(0,0,0,0.04)',
            },
            '&::-webkit-scrollbar-thumb': {
              backgroundColor: 'rgba(0,0,0,0.2)',
              borderRadius: '4px',
              '&:hover': {
                backgroundColor: 'rgba(0,0,0,0.3)',
              }
            }
          }}
        >
          {messages.length === 0 ? (
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                alignItems: 'center', 
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
                px: 4
              }}
            >
              <Typography variant="h5" color="text.secondary" sx={{ mb: 2, fontWeight: 300 }}>
                Welcome to Chat
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 600 }}>
                Start a conversation with our AI assistant. Ask questions, request help with tasks, or explore ideas together.
              </Typography>
            </Box>
          ) : (
            <>
              {messages.map((message, index) => {
                // Calculate message order for assistant messages (1st, 2nd, etc.)
                let messageOrder: number | undefined;
                if (message.role === 'assistant') {
                  const assistantMessages = messages.slice(0, index + 1).filter(m => m.role === 'assistant');
                  messageOrder = assistantMessages.length;
                }
                
                return (
                  <ChatMessage 
                    key={message.id} 
                    message={message}
                    messageOrder={messageOrder}
                    onRetry={() => handleSendMessage(message.content)}
                    onFeedbackChange={() => {
                      // Optionally refresh messages or update UI
                      console.log('Feedback changed for message:', message.id);
                    }}
                  />
                );
              })}
              {isLoading && (
                <Box 
                  sx={{ 
                    py: 3,
                    px: { xs: 2, sm: 4, md: 6 },
                    display: 'flex',
                    justifyContent: 'flex-start'
                  }}
                >
                  <Box
                    sx={{
                      maxWidth: '100%',
                      borderLeft: '3px solid #1976d2',
                      backgroundColor: 'rgba(76, 175, 80, 0.02)',
                      py: 2,
                      px: 3,
                      borderRadius: 1
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                      <BotIcon sx={{ fontSize: 20, color: 'primary.main', mr: 1 }} />
                      <Typography variant="subtitle2" sx={{ fontWeight: 600, color: 'primary.main', fontSize: '0.875rem' }}>
                        Assistant
                      </Typography>
                    </Box>
                    <Box sx={{ pl: 4, display: 'flex', alignItems: 'center' }}>
                      <Box
                        sx={{
                          display: 'inline-flex',
                          mr: 2,
                          '& > div': {
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: 'primary.main',
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
                      <Typography variant="body2" color="text.secondary">
                        Thinking...
                      </Typography>
                    </Box>
                  </Box>
                </Box>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </Box>

        <Divider />

        {/* Enhanced Input Area */}
        <Box p={2}>
          <ChatInput
            onSend={handleSendMessage}
            disabled={isLoading}
            settings={chatSettings}
            onSettingsChange={handleSettingsChange}
            onAddDocument={handleAddDocument}
          />
        </Box>
      </Box>

      <Divider orientation="vertical" flexItem />

      {/* Context Panel */}
      <Box width={350}>
        <ContextPanel 
          context={context}
          sessionId={currentSession?.id}
          onUpdateContext={updateContext}
        />
      </Box>
    </Box>
  );
};

export default ChatView;