// WebSocket 消息类型定义

// 服务器到客户端的消息类型
export interface SystemMessage {
  type: 'system_message';
  payload: {
    message: string;
  };
}

export interface AIResponseChunk {
  type: 'ai_response_chunk';
  payload: {
    chunk: string;
  };
}

export interface EvaluationUpdate {
  type: 'evaluation_update';
  payload: {
    message: string;
    extracted_traits?: string[];
    is_ready?: boolean;
  };
}

export interface ConfirmationRequest {
  type: 'confirmation_request';
  payload: {
    reason: string;
  };
}

export interface FinalPromptChunk {
  type: 'final_prompt_chunk';
  payload: {
    chunk: string;
  };
}

export interface SessionEnd {
  type: 'session_end';
  payload: {
    message: string;
  };
}

export interface ErrorMessage {
  type: 'error';
  payload: {
    message: string;
  };
}

// API配置相关消息类型
export interface ApiConfigResult {
  type: 'api_config_result';
  payload: {
    success: boolean;
    message: string;
  };
}

// 客户端到服务器的消息类型
export interface UserResponse {
  type: 'user_response';
  payload: {
    answer: string;
  };
}

export interface UserConfirmation {
  type: 'user_confirmation';
  payload: {
    confirm: boolean;
  };
}

export interface ApiConfig {
  type: 'api_config';
  payload: {
    api_type: 'gemini' | 'openai';
    api_key?: string;
    base_url?: string;
    model?: string;
    evaluator_model?: string; // Gemini专用评估模型
    temperature?: number;
    max_tokens?: number;
    nsfw_mode?: boolean;
  };
}

export interface StartSession {
  type: 'start_session';
  payload: object;
}

// 联合类型定义
export type ServerMessage =
  | SystemMessage
  | AIResponseChunk
  | EvaluationUpdate
  | ConfirmationRequest
  | FinalPromptChunk
  | SessionEnd
  | ErrorMessage
  | ApiConfigResult;

export type ClientMessage = UserResponse | UserConfirmation | ApiConfig | StartSession;

export type WebSocketMessage = ServerMessage | ClientMessage;

// 类型保护函数
export function isSystemMessage(message: WebSocketMessage): message is SystemMessage {
  return message.type === 'system_message';
}

export function isAIResponseChunk(message: WebSocketMessage): message is AIResponseChunk {
  return message.type === 'ai_response_chunk';
}

export function isEvaluationUpdate(message: WebSocketMessage): message is EvaluationUpdate {
  return message.type === 'evaluation_update';
}

export function isConfirmationRequest(message: WebSocketMessage): message is ConfirmationRequest {
  return message.type === 'confirmation_request';
}

export function isFinalPromptChunk(message: WebSocketMessage): message is FinalPromptChunk {
  return message.type === 'final_prompt_chunk';
}

export function isSessionEnd(message: WebSocketMessage): message is SessionEnd {
  return message.type === 'session_end';
}

export function isErrorMessage(message: WebSocketMessage): message is ErrorMessage {
  return message.type === 'error';
}

export function isApiConfigResult(message: WebSocketMessage): message is ApiConfigResult {
  return message.type === 'api_config_result';
}

// 聊天消息界面显示类型
export interface ChatMessage {
  id: string;
  type: 'system' | 'ai' | 'user' | 'final_prompt' | 'error';
  content: string;
  timestamp: Date;
  isComplete?: boolean; // 用于标识流式消息是否完成
}

// WebSocket 连接状态
export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

// 应用状态
export type AppState = 'initial' | 'chatting' | 'awaiting_confirmation' | 'generating_final_prompt' | 'completed' | 'error';

// 会话管理类型
export interface Session {
  id: string;
  name: string;
  createdAt: Date;
  messageCount: number;
  status: 'active' | 'completed' | 'paused';
  lastMessage?: string;
  messages: ChatMessage[];
}
