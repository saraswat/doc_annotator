import { ChatSession, ChatMessage, ChatMessageCreate, StreamingResponse } from '../types/chat';
import apiService from './api';

class ChatService {
  async createSession(title?: string): Promise<ChatSession> {
    const response = await apiService.post('/chat/sessions', { title });
    return response.data;
  }

  async getSessions(): Promise<ChatSession[]> {
    const response = await apiService.get('/chat/sessions');
    return response.data;
  }

  async getSession(sessionId: string): Promise<ChatSession> {
    const response = await apiService.get(`/chat/sessions/${sessionId}`);
    return response.data;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await apiService.delete(`/chat/sessions/${sessionId}`);
  }

  async archiveSession(sessionId: string): Promise<ChatSession> {
    const response = await apiService.post(`/chat/sessions/${sessionId}/archive`);
    return response.data;
  }

  async sendMessage(sessionId: string, messageData: ChatMessageCreate): Promise<ReadableStream> {
    // Use fetch for streaming response instead of axios
    const response = await fetch(
      `${apiService.getBaseURL()}/chat/sessions/${sessionId}/messages`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(messageData)
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.body!;
  }

  async *streamResponse(stream: ReadableStream): AsyncGenerator<StreamingResponse> {
    const reader = stream.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data as StreamingResponse;
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  async getContext(sessionId: string): Promise<any> {
    const response = await apiService.get(`/chat/sessions/${sessionId}/context`);
    return response.data;
  }

  async updateContext(sessionId: string, updates: any): Promise<any> {
    const response = await apiService.patch(`/chat/sessions/${sessionId}/context`, updates);
    return response.data;
  }
}

export default new ChatService();