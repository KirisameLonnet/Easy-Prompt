/**
 * REST API Service for Session Management
 * 会话管理的REST API服务
 */
import type { Session, SessionCreate, SessionUpdate, ChatMessage, EvaluationData } from 'src/types/websocket';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export interface ApiResponse<T = unknown> {
  success: boolean;
  message: string;
  data?: T;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T = unknown>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${endpoint}`;

    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, { ...defaultOptions, ...options });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || `HTTP error! status: ${response.status}`);
      }

      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Session Management Methods
  async createSession(sessionData?: SessionCreate): Promise<Session> {
    const response = await this.request<Session>('/sessions/', {
      method: 'POST',
      body: JSON.stringify(sessionData || {}),
    });
    return response.data!;
  }

  async getAllSessions(): Promise<Session[]> {
    const response = await this.request<Session[]>('/sessions/');
    return response.data!;
  }

  async getSession(sessionId: string): Promise<Session> {
    const response = await this.request<Session>(`/sessions/${sessionId}`);
    return response.data!;
  }

  async updateSession(sessionId: string, sessionData: SessionUpdate): Promise<Session> {
    const response = await this.request<Session>(`/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(sessionData),
    });
    return response.data!;
  }

  async deleteSession(sessionId: string): Promise<void> {
    await this.request(`/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  async addMessageToSession(sessionId: string, message: ChatMessage): Promise<Session> {
    const response = await this.request<Session>(`/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(message),
    });
    return response.data!;
  }

  async updateSessionEvaluation(sessionId: string, evaluationData: EvaluationData): Promise<Session> {
    const response = await this.request<Session>(`/sessions/${sessionId}/evaluation`, {
      method: 'PUT',
      body: JSON.stringify(evaluationData),
    });
    return response.data!;
  }

  async getSessionMessages(sessionId: string): Promise<ChatMessage[]> {
    const response = await this.request<ChatMessage[]>(`/sessions/${sessionId}/messages`);
    return response.data!;
  }

  async getSessionEvaluation(sessionId: string): Promise<EvaluationData | null> {
    const response = await this.request<EvaluationData>(`/sessions/${sessionId}/evaluation`);
    return response.data || null;
  }
}

export const apiService = new ApiService();
