import { useState, useCallback } from 'react';
import { ChatSession, ChatMessage, ChatMessageCreate, StreamingResponse } from '../types/chat';
import chatService from '../services/chatService';

interface UseChatReturn {
  loading: boolean;
  error: string | null;
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  messages: ChatMessage[];
  sendMessage: (messageData: ChatMessageCreate) => Promise<void>;
  createSession: (title?: string) => Promise<ChatSession>;
  loadSession: (sessionId: string) => Promise<ChatSession>;
  loadSessions: () => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  streamResponse: (stream: ReadableStream, onChunk: (chunk: string) => void) => Promise<void>;
  clearError: () => void;
}

export const useChat = (): UseChatReturn => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const createSession = useCallback(async (title?: string): Promise<ChatSession> => {
    try {
      setLoading(true);
      setError(null);
      const session = await chatService.createSession(title);
      setCurrentSession(session);
      setMessages([]);
      return session;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create session';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string): Promise<ChatSession> => {
    try {
      setLoading(true);
      setError(null);
      const session = await chatService.getSession(sessionId);
      setCurrentSession(session);
      // Load messages separately
      const messages = await chatService.getSessionMessages(sessionId);
      setMessages(messages || []);
      return session;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load session';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadSessions = useCallback(async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      const sessionsList = await chatService.getSessions();
      setSessions(sessionsList);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to load sessions';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const deleteSession = useCallback(async (sessionId: string): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      await chatService.deleteSession(sessionId);
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (currentSession?.id === sessionId) {
        setCurrentSession(null);
        setMessages([]);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete session';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [currentSession?.id]);

  const sendMessage = useCallback(async (messageData: ChatMessageCreate): Promise<void> => {
    if (!currentSession) {
      throw new Error('No active session');
    }

    try {
      setError(null);
      const stream = await chatService.sendMessage(currentSession.id, messageData);
      
      // Process streaming response will be handled by the calling component
      // This just initiates the stream
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMsg);
      throw err;
    }
  }, [currentSession]);

  const streamResponse = useCallback(async (
    stream: ReadableStream,
    onChunk: (chunk: string) => void
  ): Promise<void> => {
    try {
      for await (const response of chatService.streamResponse(stream)) {
        if (response.type === 'chunk' && response.content) {
          onChunk(response.content);
        } else if (response.type === 'error') {
          throw new Error(response.error || 'Stream error');
        }
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Streaming failed';
      setError(errorMsg);
      throw err;
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    loading,
    error,
    sessions,
    currentSession,
    messages,
    sendMessage,
    createSession,
    loadSession,
    loadSessions,
    deleteSession,
    streamResponse,
    clearError
  };
};