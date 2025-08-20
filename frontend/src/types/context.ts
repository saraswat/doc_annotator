import { Task, ProblemContext } from './chat';

export interface ContextUpdate {
  sessionId?: string;
  summary?: string;
  currentGoal?: string;
  tasks?: Task[];
  relevantDocuments?: string[];
}

export interface ContextManagerHook {
  context: ProblemContext | null;
  loading: boolean;
  error: string | null;
  updateContext: (updates: ContextUpdate) => Promise<void>;
  extractTasksFromMessage: (message: string) => Task[];
  refreshContext: (sessionId: string) => Promise<void>;
}

export interface ViewState {
  currentView: 'documents' | 'chat';
  currentDocumentId?: string;
  currentChatSessionId?: string;
}

export interface ViewContextType {
  viewState: ViewState;
  setCurrentView: (view: 'documents' | 'chat') => void;
  setCurrentDocument: (documentId?: string) => void;
  setCurrentChatSession: (sessionId?: string) => void;
}