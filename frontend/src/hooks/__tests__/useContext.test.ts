import { renderHook, act } from '@testing-library/react';
import { useContext } from '../useContext';
import chatService from '../../services/chatService';

// Mock the chat service
jest.mock('../../services/chatService');
const mockedChatService = chatService as jest.Mocked<typeof chatService>;

describe('useContext Hook', () => {
  const mockContext = {
    sessionId: 'test-session-id',
    summary: 'Test conversation context',
    currentGoal: 'Fix authentication issues',
    tasks: [
      {
        id: 'task-1',
        description: 'Review authentication code',
        status: 'pending' as const,
        priority: 'high' as const,
        createdAt: new Date()
      },
      {
        id: 'task-2',
        description: 'Write unit tests',
        status: 'completed' as const,
        priority: 'medium' as const,
        createdAt: new Date()
      }
    ],
    relevantDocuments: ['auth.js', 'user.model.js'],
    createdAt: new Date(),
    updatedAt: new Date()
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Initial State', () => {
    it('initializes with default values', () => {
      const { result } = renderHook(() => useContext());

      expect(result.current.context).toBeNull();
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  describe('Context Management', () => {
    describe('updateContext', () => {
      it('updates context successfully', async () => {
        const updatedContext = {
          ...mockContext,
          summary: 'Updated summary'
        };
        
        mockedChatService.updateContext.mockResolvedValue(updatedContext);

        const { result } = renderHook(() => useContext());

        // Set initial context
        act(() => {
          result.current.context = mockContext;
        });

        await act(async () => {
          await result.current.updateContext({
            summary: 'Updated summary'
          });
        });

        expect(result.current.context).toEqual(updatedContext);
        expect(mockedChatService.updateContext).toHaveBeenCalledWith(
          'test-session-id',
          { summary: 'Updated summary' }
        );
        expect(result.current.error).toBeNull();
      });

      it('throws error when no active context session', async () => {
        const { result } = renderHook(() => useContext());

        await act(async () => {
          try {
            await result.current.updateContext({ summary: 'New summary' });
          } catch (error) {
            expect(error).toEqual(new Error('No active context session'));
          }
        });

        expect(result.current.error).toBe('Failed to update context');
      });

      it('throws error when context has no sessionId', async () => {
        const { result } = renderHook(() => useContext());

        // Set context without sessionId
        act(() => {
          result.current.context = {
            ...mockContext,
            sessionId: ''
          };
        });

        await act(async () => {
          try {
            await result.current.updateContext({ summary: 'New summary' });
          } catch (error) {
            expect(error).toEqual(new Error('No active context session'));
          }
        });
      });

      it('handles update error from service', async () => {
        const error = new Error('Context update failed');
        mockedChatService.updateContext.mockRejectedValue(error);

        const { result } = renderHook(() => useContext());

        // Set initial context
        act(() => {
          result.current.context = mockContext;
        });

        await act(async () => {
          try {
            await result.current.updateContext({ summary: 'New summary' });
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to update context');
      });

      it('sets loading state during update', async () => {
        let resolvePromise: (value: any) => void;
        const promise = new Promise((resolve) => {
          resolvePromise = resolve;
        });
        mockedChatService.updateContext.mockReturnValue(promise as any);

        const { result } = renderHook(() => useContext());

        // Set initial context
        act(() => {
          result.current.context = mockContext;
        });

        act(() => {
          result.current.updateContext({ summary: 'New summary' });
        });

        expect(result.current.loading).toBe(true);

        await act(async () => {
          resolvePromise!(mockContext);
        });

        expect(result.current.loading).toBe(false);
      });
    });

    describe('refreshContext', () => {
      it('refreshes context successfully', async () => {
        mockedChatService.getContext.mockResolvedValue(mockContext);

        const { result } = renderHook(() => useContext());

        await act(async () => {
          await result.current.refreshContext('test-session-id');
        });

        expect(result.current.context).toEqual(mockContext);
        expect(mockedChatService.getContext).toHaveBeenCalledWith('test-session-id');
        expect(result.current.error).toBeNull();
      });

      it('handles refresh error from service', async () => {
        const error = new Error('Context refresh failed');
        mockedChatService.getContext.mockRejectedValue(error);

        const { result } = renderHook(() => useContext());

        await act(async () => {
          try {
            await result.current.refreshContext('test-session-id');
          } catch (e) {
            expect(e).toEqual(error);
          }
        });

        expect(result.current.error).toBe('Failed to refresh context');
      });

      it('sets loading state during refresh', async () => {
        let resolvePromise: (value: any) => void;
        const promise = new Promise((resolve) => {
          resolvePromise = resolve;
        });
        mockedChatService.getContext.mockReturnValue(promise as any);

        const { result } = renderHook(() => useContext());

        act(() => {
          result.current.refreshContext('test-session-id');
        });

        expect(result.current.loading).toBe(true);

        await act(async () => {
          resolvePromise!(mockContext);
        });

        expect(result.current.loading).toBe(false);
      });
    });
  });

  describe('Task Extraction', () => {
    describe('extractTasksFromMessage', () => {
      it('extracts tasks from bullet point messages', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        Here's what we need to do:
        - Review the authentication code
        - Write comprehensive unit tests
        - Update the documentation
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(3);
        expect(tasks[0].description).toBe('Review the authentication code');
        expect(tasks[1].description).toBe('Write comprehensive unit tests');
        expect(tasks[2].description).toBe('Update the documentation');
        
        tasks.forEach(task => {
          expect(task.status).toBe('pending');
          expect(task.priority).toMatch(/low|medium|high/);
          expect(task.createdAt).toBeInstanceOf(Date);
          expect(task.id).toBeDefined();
        });
      });

      it('extracts tasks from numbered list messages', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        Action items:
        1. Fix the login validation bug
        2. Implement password strength checking
        3. Add two-factor authentication
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(3);
        expect(tasks[0].description).toBe('Fix the login validation bug');
        expect(tasks[1].description).toBe('Implement password strength checking');
        expect(tasks[2].description).toBe('Add two-factor authentication');
      });

      it('extracts tasks from TODO markers', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        TODO: Refactor the authentication module
        Task: Write integration tests
        Action: Deploy to staging environment
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(3);
        expect(tasks[0].description).toBe('Refactor the authentication module');
        expect(tasks[1].description).toBe('Write integration tests');
        expect(tasks[2].description).toBe('Deploy to staging environment');
      });

      it('filters out very short task descriptions', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        - Fix
        - This is a proper task description that should be included
        - Do
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(1);
        expect(tasks[0].description).toBe('This is a proper task description that should be included');
      });

      it('filters out very long task descriptions', () => {
        const { result } = renderHook(() => useContext());

        const longDescription = 'a'.repeat(250); // 250 characters
        const message = `
        - Short task
        - ${longDescription}
        - Another short task
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(2);
        expect(tasks[0].description).toBe('Short task');
        expect(tasks[1].description).toBe('Another short task');
      });

      it('limits tasks to maximum of 10', () => {
        const { result } = renderHook(() => useContext());

        const taskLines = Array.from({ length: 15 }, (_, i) => 
          `- Task number ${i + 1} that should be extracted`
        ).join('\n');

        const tasks = result.current.extractTasksFromMessage(taskLines);

        expect(tasks).toHaveLength(10);
      });

      it('determines priority based on keywords', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        - Fix this critical bug immediately (urgent)
        - Consider adding this feature eventually
        - Review the code changes
        - This is a high priority task
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        const urgentTask = tasks.find(t => t.description.includes('critical'));
        const lowPriorityTask = tasks.find(t => t.description.includes('eventually'));
        const highPriorityTask = tasks.find(t => t.description.includes('high priority'));

        expect(urgentTask?.priority).toBe('high');
        expect(lowPriorityTask?.priority).toBe('low');
        expect(highPriorityTask?.priority).toBe('high');
      });

      it('returns empty array for messages without actionable items', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        This is just a regular conversation message.
        There are no action items or tasks mentioned here.
        Just discussion about the weather and other topics.
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks).toHaveLength(0);
      });

      it('handles mixed formats in one message', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        Here's our plan:
        
        Phase 1:
        1. Review existing code
        2. Identify security issues
        
        Next steps:
        - Write unit tests
        - Update documentation
        
        TODO: Deploy to production
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        expect(tasks.length).toBeGreaterThanOrEqual(5);
        
        const descriptions = tasks.map(t => t.description);
        expect(descriptions).toContain('Review existing code');
        expect(descriptions).toContain('Write unit tests');
        expect(descriptions).toContain('Deploy to production');
      });

      it('assigns unique IDs to each task', () => {
        const { result } = renderHook(() => useContext());

        const message = `
        - First task
        - Second task
        - Third task
        `;

        const tasks = result.current.extractTasksFromMessage(message);

        const ids = tasks.map(t => t.id);
        const uniqueIds = new Set(ids);
        
        expect(uniqueIds.size).toBe(tasks.length);
        
        tasks.forEach(task => {
          expect(task.id).toMatch(/^task-\d+-[\d.]+$/);
        });
      });
    });
  });

  describe('Priority Determination', () => {
    it('correctly identifies high priority keywords', () => {
      const { result } = renderHook(() => useContext());

      const highPriorityMessages = [
        '- Fix this urgent security vulnerability',
        '- Critical bug needs immediate attention',
        '- High priority feature request',
        '- ASAP - resolve the database issue'
      ];

      highPriorityMessages.forEach(message => {
        const tasks = result.current.extractTasksFromMessage(message);
        expect(tasks[0]?.priority).toBe('high');
      });
    });

    it('correctly identifies low priority keywords', () => {
      const { result } = renderHook(() => useContext());

      const lowPriorityMessages = [
        '- Eventually we should refactor this',
        '- Consider adding this nice to have feature',
        '- Maybe we could improve the UI',
        '- Optional enhancement for later'
      ];

      lowPriorityMessages.forEach(message => {
        const tasks = result.current.extractTasksFromMessage(message);
        expect(tasks[0]?.priority).toBe('low');
      });
    });

    it('defaults to medium priority', () => {
      const { result } = renderHook(() => useContext());

      const message = '- Complete the code review process';
      const tasks = result.current.extractTasksFromMessage(message);

      expect(tasks[0]?.priority).toBe('medium');
    });
  });

  describe('Error Handling', () => {
    it('handles extraction errors gracefully', () => {
      const { result } = renderHook(() => useContext());

      // Test with null/undefined message
      expect(() => {
        result.current.extractTasksFromMessage(null as any);
      }).not.toThrow();

      expect(() => {
        result.current.extractTasksFromMessage(undefined as any);
      }).not.toThrow();
    });
  });

  describe('State Management', () => {
    it('maintains consistent error states', async () => {
      const { result } = renderHook(() => useContext());

      // Set initial context
      act(() => {
        result.current.context = mockContext;
      });

      // Trigger an error
      const error = new Error('Service error');
      mockedChatService.updateContext.mockRejectedValue(error);

      await act(async () => {
        try {
          await result.current.updateContext({ summary: 'New summary' });
        } catch (e) {
          // Error is expected
        }
      });

      expect(result.current.error).toBe('Failed to update context');
      expect(result.current.loading).toBe(false);

      // Successful operation should clear error
      mockedChatService.updateContext.mockResolvedValue(mockContext);

      await act(async () => {
        await result.current.updateContext({ summary: 'Another summary' });
      });

      expect(result.current.error).toBeNull();
    });
  });
});