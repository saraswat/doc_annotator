import { useState, useCallback } from 'react';
import { ProblemContext, Task } from '../types/chat';
import { ContextUpdate, ContextManagerHook } from '../types/context';
import chatService from '../services/chatService';

export const useContext = (): ContextManagerHook => {
  const [context, setContext] = useState<ProblemContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateContext = useCallback(async (updates: ContextUpdate): Promise<void> => {
    if (!context || !context.sessionId) {
      throw new Error('No active context session');
    }

    try {
      setLoading(true);
      setError(null);
      const updatedContext = await chatService.updateContext(context.sessionId, updates);
      setContext(updatedContext);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update context';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [context]);

  const refreshContext = useCallback(async (sessionId: string): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      const contextData = await chatService.getContext(sessionId);
      setContext(contextData);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to refresh context';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const extractTasksFromMessage = useCallback((message: string): Task[] => {
    const tasks: Task[] = [];
    
    // Simple regex patterns to extract tasks
    const taskPatterns = [
      /(?:^|\n)\s*[-•]\s+(.+?)(?:\n|$)/gm, // Bullet points
      /(?:^|\n)\s*\d+\.\s+(.+?)(?:\n|$)/gm, // Numbered lists
      /(?:TODO|Task|Action):\s*(.+?)(?:\n|$)/gm, // Explicit markers
    ];

    taskPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(message)) !== null) {
        const taskText = match[1].trim();
        if (taskText.length > 10 && taskText.length < 200) {
          tasks.push({
            id: `task-${Date.now()}-${Math.random()}`,
            description: taskText,
            status: 'pending',
            priority: determinePriority(taskText),
            createdAt: new Date()
          });
        }
      }
    });

    return tasks.slice(0, 10); // Limit to 10 tasks
  }, []);

  return {
    context,
    loading,
    error,
    updateContext,
    extractTasksFromMessage,
    refreshContext
  };
};

function determinePriority(taskText: string): 'low' | 'medium' | 'high' {
  const text = taskText.toLowerCase();
  
  const highPriorityKeywords = ['urgent', 'critical', 'immediately', 'asap', 'priority'];
  const lowPriorityKeywords = ['eventually', 'consider', 'maybe', 'optional', 'nice to have'];
  
  if (highPriorityKeywords.some(keyword => text.includes(keyword))) {
    return 'high';
  }
  
  if (lowPriorityKeywords.some(keyword => text.includes(keyword))) {
    return 'low';
  }
  
  return 'medium';
}