export interface ChatSession {
  id: string;
  userId: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  lastMessage?: string;
  messageCount: number;
  status: 'active' | 'archived';
  metadata?: {
    documentIds?: string[];
    model?: string;
    settings?: ChatSettings;
  };
}

export interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    tokens?: number;
    documentReferences?: DocumentReference[];
    annotations?: string[];
  };
  status: 'sending' | 'sent' | 'error';
}

export interface ChatSettings {
  model: string;
  temperature: number;
  maxTokens: number;
  webBrowsing: boolean;
  deepResearch: boolean;
  includeDocuments: string[];
}

export interface ProblemContext {
  sessionId: string;
  summary: string;
  currentGoal?: string;
  tasks: Task[];
  relevantDocuments?: string[];
  updatedAt: Date;
}

export interface Task {
  id: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed';
  priority: 'low' | 'medium' | 'high';
  createdAt: Date;
  completedAt?: Date;
}

export interface DocumentReference {
  documentId: string;
  documentName: string;
  relevantSection?: string;
  confidence: number;
}

// API Request/Response types
export interface ChatMessageCreate {
  content: string;
  settings: ChatSettings;
  context_options: {
    problemContext?: ProblemContext;
    documentIds?: string[];
    enableWebBrowsing?: boolean;
    enableDeepResearch?: boolean;
  };
}

export interface StreamingResponse {
  type: 'chunk' | 'context_update' | 'complete' | 'error';
  content?: string;
  messageId?: string;
  context?: ProblemContext;
  error?: string;
  tokens?: number;
}