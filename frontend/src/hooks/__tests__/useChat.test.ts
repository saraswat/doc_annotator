import { renderHook, act } from '@testing-library/react';
import { useChat } from '../useChat';
import chatService from '../../services/chatService';

// Mock the chat service
jest.mock('../../services/chatService');
const mockedChatService = chatService as jest.Mocked<typeof chatService>;

describe('useChat Hook', () => {
  const mockSession = {
    id: 'test-session-id',
    userId: '1',
    title: 'Test Session',
    createdAt: new Date(),
    updatedAt: new Date(),
    lastMessage: 'Last message',
    messageCount: 2,
    status: 'active' as const,
    metadata: {}
  };

  const mockMessage = {
    id: 'msg-1',
    sessionId: 'test-session-id',
    role: 'user' as const,
    content: 'Hello',
    timestamp: new Date(),
    status: 'sent' as const
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    it('initializes with default values', () => {
      const { result } = renderHook(() => useChat());

      expect(result.current.sessions).toEqual([]);
      expect(result.current.currentSession).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.messages).toEqual([]);
    });
  });

  describe('Session Management', () => {
    describe('createSession', () => {
      it('creates a new session successfully', async () => {
        mockedChatService.createSession.mockResolvedValue(mockSession);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          const session = await result.current.createSession('Test Session');
          expect(session).toEqual(mockSession);
        });

        expect(result.current.currentSession).toEqual(mockSession);
        expect(result.current.messages).toEqual([]);
        expect(result.current.error).toBeNull();
        expect(mockedChatService.createSession).toHaveBeenCalledWith('Test Session');
      });

      it('creates session without title', async () => {
        mockedChatService.createSession.mockResolvedValue(mockSession);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          await result.current.createSession();
        });

        expect(mockedChatService.createSession).toHaveBeenCalledWith(undefined);
      });

      it('handles session creation error', async () => {
        const error = new Error('Failed to create session');
        mockedChatService.createSession.mockRejectedValue(error);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.createSession('Test Session');
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to create session');
        expect(result.current.currentSession).toBeNull();
      });

      it('sets loading state during creation', async () => {
        let resolvePromise: (value: any) => void;
        const promise = new Promise((resolve) => {
          resolvePromise = resolve;
        });
        mockedChatService.createSession.mockReturnValue(promise as any);

        const { result } = renderHook(() => useChat());

        act(() => {
          result.current.createSession('Test Session');
        });

        expect(result.current.loading).toBe(true);

        await act(async () => {
          resolvePromise!(mockSession);
        });

        expect(result.current.loading).toBe(false);
      });
    });

    describe('loadSession', () => {
      it('loads an existing session successfully', async () => {
        const sessionWithMessages = {
          ...mockSession,
          messages: [mockMessage]
        };
        mockedChatService.getSession.mockResolvedValue(sessionWithMessages);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          const session = await result.current.loadSession('test-session-id');
          expect(session).toEqual(sessionWithMessages);
        });

        expect(result.current.currentSession).toEqual(sessionWithMessages);
        expect(result.current.messages).toEqual([mockMessage]);
        expect(mockedChatService.getSession).toHaveBeenCalledWith('test-session-id');
      });

      it('handles session loading error', async () => {
        const error = new Error('Session not found');
        mockedChatService.getSession.mockRejectedValue(error);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.loadSession('non-existent-id');
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Session not found');
      });

      it('updates sessions list when loading session', async () => {
        mockedChatService.getSession.mockResolvedValue(mockSession);

        const { result } = renderHook(() => useChat());

        // First, set some existing sessions
        act(() => {
          result.current.sessions.push({
            ...mockSession,
            id: 'different-session'
          });
        });

        await act(async () => {
          await result.current.loadSession('test-session-id');
        });

        expect(result.current.sessions).toContainEqual(mockSession);
      });
    });

    describe('loadSessions', () => {
      it('loads user sessions successfully', async () => {
        const sessions = [mockSession, { ...mockSession, id: 'session-2', title: 'Session 2' }];
        mockedChatService.getSessions.mockResolvedValue(sessions);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          const loadedSessions = await result.current.loadSessions();
          expect(loadedSessions).toEqual(sessions);
        });

        expect(result.current.sessions).toEqual(sessions);
        expect(mockedChatService.getSessions).toHaveBeenCalled();
      });

      it('handles sessions loading error', async () => {
        const error = new Error('Failed to load sessions');
        mockedChatService.getSessions.mockRejectedValue(error);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.loadSessions();
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to load sessions');
      });
    });

    describe('deleteSession', () => {
      it('deletes a session successfully', async () => {
        mockedChatService.deleteSession.mockResolvedValue(undefined);

        const { result } = renderHook(() => useChat());

        // Set up initial state
        act(() => {
          result.current.sessions.push(mockSession);
          result.current.currentSession = mockSession;
          result.current.messages = [mockMessage];
        });

        await act(async () => {
          await result.current.deleteSession('test-session-id');
        });

        expect(result.current.sessions).not.toContainEqual(mockSession);
        expect(result.current.currentSession).toBeNull();
        expect(result.current.messages).toEqual([]);
        expect(mockedChatService.deleteSession).toHaveBeenCalledWith('test-session-id');
      });

      it('handles session deletion error', async () => {
        const error = new Error('Failed to delete session');
        mockedChatService.deleteSession.mockRejectedValue(error);

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.deleteSession('test-session-id');
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to delete session');
      });

      it('only clears current session if it matches deleted session', async () => {
        mockedChatService.deleteSession.mockResolvedValue(undefined);

        const { result } = renderHook(() => useChat());
        const differentSession = { ...mockSession, id: 'different-session' };

        // Set current session to a different one
        act(() => {
          result.current.sessions.push(mockSession, differentSession);
          result.current.currentSession = differentSession;
          result.current.messages = [mockMessage];
        });

        await act(async () => {
          await result.current.deleteSession('test-session-id');
        });

        // Current session should remain unchanged
        expect(result.current.currentSession).toEqual(differentSession);
        expect(result.current.messages).toEqual([mockMessage]);
        expect(result.current.sessions).toEqual([differentSession]);
      });
    });
  });

  describe('Message Handling', () => {
    describe('sendMessage', () => {
      it('sends a message successfully', async () => {
        const mockStream = new ReadableStream();
        mockedChatService.sendMessage.mockResolvedValue(mockStream);

        const { result } = renderHook(() => useChat());

        // Set current session
        act(() => {
          result.current.currentSession = mockSession;
        });

        const messageData = {
          content: 'Hello',
          settings: {
            model: 'test_model',
            temperature: 0.7,
            maxTokens: 2000,
            webBrowsing: false,
            deepResearch: false,
            includeDocuments: []
          },
          context_options: {}
        };

        await act(async () => {
          await result.current.sendMessage(messageData);
        });

        expect(mockedChatService.sendMessage).toHaveBeenCalledWith('test-session-id', messageData);
      });

      it('throws error when no active session', async () => {
        const { result } = renderHook(() => useChat());

        const messageData = {
          content: 'Hello',
          settings: {
            model: 'test_model',
            temperature: 0.7,
            maxTokens: 2000,
            webBrowsing: false,
            deepResearch: false,
            includeDocuments: []
          },
          context_options: {}
        };

        await act(async () => {
          try {
            await result.current.sendMessage(messageData);
          } catch (error) {
            expect(error).toEqual(new Error('No active session'));
          }
        });
      });

      it('handles message sending error', async () => {
        const error = new Error('Failed to send message');
        mockedChatService.sendMessage.mockRejectedValue(error);

        const { result } = renderHook(() => useChat());

        // Set current session
        act(() => {
          result.current.currentSession = mockSession;
        });

        const messageData = {
          content: 'Hello',
          settings: {
            model: 'test_model',
            temperature: 0.7,
            maxTokens: 2000,
            webBrowsing: false,
            deepResearch: false,
            includeDocuments: []
          },
          context_options: {}
        };

        await act(async () => {
          try {
            await result.current.sendMessage(messageData);
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to send message');
      });
    });

    describe('streamResponse', () => {
      it('processes streaming response successfully', async () => {
        const mockStream = new ReadableStream();
        const mockOnChunk = jest.fn();

        // Mock the streaming response generator
        const mockResponseGenerator = async function* () {
          yield { type: 'chunk' as const, content: 'Hello' };
          yield { type: 'chunk' as const, content: ' world!' };
          yield { type: 'complete' as const, content: '' };
        };

        mockedChatService.streamResponse.mockReturnValue(mockResponseGenerator());

        const { result } = renderHook(() => useChat());

        await act(async () => {
          await result.current.streamResponse(mockStream, mockOnChunk);
        });

        expect(mockOnChunk).toHaveBeenCalledWith('Hello');
        expect(mockOnChunk).toHaveBeenCalledWith(' world!');
        expect(mockOnChunk).toHaveBeenCalledTimes(2);
      });

      it('handles streaming error', async () => {
        const mockStream = new ReadableStream();
        const mockOnChunk = jest.fn();

        // Mock the streaming response generator with error
        const mockResponseGenerator = async function* () {
          yield { type: 'chunk' as const, content: 'Hello' };
          yield { type: 'error' as const, error: 'Stream error' };
        };

        mockedChatService.streamResponse.mockReturnValue(mockResponseGenerator());

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.streamResponse(mockStream, mockOnChunk);
          } catch (error) {
            expect(error).toEqual(new Error('Stream error'));
          }
        });

        expect(result.current.error).toBe('Streaming failed');
      });

      it('handles streaming service error', async () => {
        const mockStream = new ReadableStream();
        const mockOnChunk = jest.fn();
        const error = new Error('Service error');

        mockedChatService.streamResponse.mockImplementation(() => {
          throw error;
        });

        const { result } = renderHook(() => useChat());

        await act(async () => {
          try {
            await result.current.streamResponse(mockStream, mockOnChunk);
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Streaming failed');
      });
    });
  });

  describe('Error Handling', () => {
    it('clears error when clearError is called', () => {
      const { result } = renderHook(() => useChat());

      // Set an error
      act(() => {
        result.current.error = 'Test error';
      });

      // Clear the error
      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Loading States', () => {
    it('manages loading state correctly during operations', async () => {
      let resolvePromise: (value: any) => void;
      const promise = new Promise((resolve) => {
        resolvePromise = resolve;
      });
      mockedChatService.createSession.mockReturnValue(promise as any);

      const { result } = renderHook(() => useChat());

      // Start async operation
      act(() => {
        result.current.createSession('Test Session');
      });

      expect(result.current.loading).toBe(true);

      // Complete async operation
      await act(async () => {
        resolvePromise!(mockSession);
      });

      expect(result.current.loading).toBe(false);
    });
  });

  describe('State Consistency', () => {
    it('maintains consistent state across operations', async () => {
      mockedChatService.createSession.mockResolvedValue(mockSession);
      mockedChatService.getSessions.mockResolvedValue([mockSession]);

      const { result } = renderHook(() => useChat());

      // Create session
      await act(async () => {
        await result.current.createSession('Test Session');
      });

      expect(result.current.currentSession).toEqual(mockSession);

      // Load sessions
      await act(async () => {
        await result.current.loadSessions();
      });

      expect(result.current.sessions).toContainEqual(mockSession);
      expect(result.current.currentSession).toEqual(mockSession);
    });
  });
});