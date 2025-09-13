import { ref, computed } from 'vue';
import type {
  WebSocketMessage,
  ChatMessage,
  ConnectionStatus,
  AppState,
  UserResponse,
  UserConfirmation,
  Session
} from 'src/types/websocket';
import {
  isSystemMessage,
  isAIResponseChunk,
  isEvaluationUpdate,
  isConfirmationRequest,
  isFinalPromptChunk,
  isSessionEnd,
  isErrorMessage,
  isApiConfigResult,
  isAuthResult
} from 'src/types/websocket';
import { apiService } from './api';

// API配置类型
export interface ApiConfig {
  api_type: 'gemini' | 'openai';
  api_key: string;
  base_url: string;
  model: string;
  evaluator_model?: string; // Gemini专用评估模型
  temperature: number;
  max_tokens: number;
  nsfw_mode: boolean;
}

// 空API配置模板
const emptyApiConfig: ApiConfig = {
  api_type: 'openai',
  api_key: '',
  base_url: '',
  model: '',
  evaluator_model: '',
  temperature: 0.7,
  max_tokens: 4000,
  nsfw_mode: false
};

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectDelay = 1000;
  private readonly websocketUrl = 'ws://127.0.0.1:8000/ws/prompt';

  // API配置状态
  private apiConfig = ref<ApiConfig | null>(null);
  private apiConfigured = ref<boolean>(false);

  // Session管理
  private currentSessionId = ref<string | null>(null);
  private sessionRestored = ref<boolean>(false);
  private sessions = ref<Session[]>([]);

  // 日志收集器
  private logBuffer: string[] = [];

  // 响应式状态
  public connectionStatus = ref<ConnectionStatus>('disconnected');
  public appState = ref<AppState>('initial');

  // 消息数据 - 严格分离不同类型的内容
  public chatMessages = ref<ChatMessage[]>([]);  // 只存储对话消息
  public evaluationStatus = ref<string>('');     // 评估状态文本
  public showEvaluationCard = ref<boolean>(false);
  public extractedTraits = ref<string[]>([]);    // 提取的角色特征列表
  public extractedKeywords = ref<string[]>([]);  // 提取的关键词
  public evaluationScore = ref<number | null>(null); // 评估分数
  public completenessData = ref<{
    core_identity: number;
    personality_traits: number;
    behavioral_patterns: number;
    interaction_patterns: number;
  }>({
    core_identity: 0,
    personality_traits: 0,
    behavioral_patterns: 0,
    interaction_patterns: 0
  }); // 完整度分解数据
  public evaluationSuggestions = ref<string[]>([]); // 改进建议
  public finalPromptContent = ref<string>('');   // 最终提示词
  public showPromptResult = ref<boolean>(false);
  public promptTimestamp = ref<Date>(new Date());
  public pendingConfirmation = ref<string>('');  // 待确认的原因

  // 当前流式消息的缓存
  private currentAIMessage = ref<ChatMessage | null>(null);
  private currentFinalPrompt = ref<ChatMessage | null>(null);

  // 计算属性 - 兼容旧的接口
  public messages = computed(() => this.chatMessages.value);

  // 日志方法
  private log(message: string, data?: unknown): void {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = `[${timestamp}] ${message}`;

    console.log(logEntry, data || '');
    this.logBuffer.push(logEntry + (data ? ` ${JSON.stringify(data)}` : ''));

    // 保持日志缓冲区大小
    if (this.logBuffer.length > 100) {
      this.logBuffer = this.logBuffer.slice(-50);
    }
  }

  // 获取日志的方法
  public getLogs(): string[] {
    return [...this.logBuffer];
  }

  // 清空日志
  public clearLogs(): void {
    this.logBuffer = [];
  }

  // API配置相关方法
  public setApiConfig(config: ApiConfig): void {
    this.apiConfig.value = config;
    this.saveApiConfig(config);
  }

  public getApiConfig(): ApiConfig | null {
    return this.apiConfig.value;
  }

  public isApiConfigured(): boolean {
    return this.apiConfigured.value;
  }

  private saveApiConfig(config: ApiConfig): void {
    try {
      localStorage.setItem('api-config', JSON.stringify(config));
    } catch (error) {
      console.error('Failed to save API config:', error);
    }
  }

  private loadApiConfig(): ApiConfig | null {
    try {
      const saved = localStorage.getItem('api-config');
      if (saved) {
        const config = JSON.parse(saved);
        // 检查配置是否包含旧的默认值，如果是则清理
        if (this.hasOldDefaultValues(config)) {
          console.log('检测到旧的默认配置，正在清理...');
          this.clearApiConfig();
          return null;
        }
        return config;
      }
    } catch (error) {
      console.error('Failed to load API config:', error);
    }
    return null;
  }

  private hasOldDefaultValues(config: ApiConfig): boolean {
    // 检查是否包含旧的DeepSeek默认配置
    return config.base_url === 'https://api.deepseek.com/v1' &&
           config.model === 'deepseek-chat';
  }

  private clearApiConfig(): void {
    try {
      localStorage.removeItem('api-config');
      console.log('已清理旧的API配置');
    } catch (error) {
      console.error('Failed to clear API config:', error);
    }
  }

  private isConfigComplete(config: ApiConfig): boolean {
    if (config.api_type === 'openai') {
      return !!(config.api_key && config.base_url && config.model);
    } else if (config.api_type === 'gemini') {
      return !!(config.api_key && config.model);
    }
    return false;
  }

  // 发送API配置到服务器
  private sendApiConfig(): void {
    if (!this.apiConfig.value || !this.ws) return;

    const configMessage = {
      type: 'api_config',
      payload: {
        api_type: this.apiConfig.value.api_type,
        api_key: this.apiConfig.value.api_key,
        base_url: this.apiConfig.value.base_url,
        model: this.apiConfig.value.model,
        evaluator_model: this.apiConfig.value.evaluator_model,
        temperature: this.apiConfig.value.temperature,
        max_tokens: this.apiConfig.value.max_tokens,
        nsfw_mode: this.apiConfig.value.nsfw_mode
      }
    };

    this.log('发送API配置', {
      ...configMessage.payload,
      api_key: configMessage.payload.api_key ? '***已设置***' : '未设置'
    });
    this.ws.send(JSON.stringify(configMessage));
  }

  // 发送认证信息
  private async sendAuthentication(): Promise<void> {
    if (!this.ws) return;

    try {
      // 导入认证服务
      const { authService } = await import('./auth');
      const token = authService.token.value;
      if (!token) {
        this.log('❌ 未找到认证令牌');
        return;
      }

      const authMessage = {
        type: 'auth',
        payload: {
          token: token
        }
      };

      this.log('发送认证信息');
      this.ws?.send(JSON.stringify(authMessage));
    } catch (error) {
      this.log('❌ 导入认证服务失败', error);
    }
  }

  // 处理认证结果
  private handleAuthResult(payload: { success: boolean; message: string; user?: { id: string; username: string; role: string } }): void {
    if (payload.success) {
      this.log('✅ 认证成功', payload.message);

      // 认证成功后，尝试加载API配置
      const savedConfig = this.loadApiConfig();
      if (savedConfig && this.isConfigComplete(savedConfig)) {
        this.apiConfig.value = savedConfig;
        this.sendApiConfig();
      } else {
        this.apiConfig.value = { ...emptyApiConfig };
        this.appState.value = 'waiting_for_config';
        this.log('⚠️ 需要配置API，等待用户输入');
      }
    } else {
      this.log('❌ 认证失败', payload.message);
      this.appState.value = 'waiting_for_auth';
    }
  }

  // 启动会话（使用默认Gemini或环境配置）
  private startSession(): void {
    if (!this.ws) return;

    const startMessage = {
      type: 'start_session',
      payload: {}
    };

    this.log('启动默认会话');
    this.ws.send(JSON.stringify(startMessage));
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.connectionStatus.value = 'connecting';

    try {
      this.ws = new WebSocket(this.websocketUrl);
      this.setupEventListeners();
    } catch (error) {
      console.error('WebSocket connection failed:', error);
      this.connectionStatus.value = 'error';
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connectionStatus.value = 'disconnected';
    this.reconnectAttempts = 0;
  }

  private setupEventListeners(): void {
    if (!this.ws) return;

    this.ws.onopen = async () => {
      console.log('WebSocket connected');
      this.connectionStatus.value = 'connected';
      this.reconnectAttempts = 0;

      // 在连接建立后，根据配置初始化会话
      await this.initializeSession();
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event);
      this.connectionStatus.value = 'disconnected';

      if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.connectionStatus.value = 'error';
    };

    this.ws.onmessage = (event) => {
      this.log('🔵 WebSocket 原始消息', event.data);

      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.log('🟢 解析后的消息', message);

        // 详细记录每种消息类型的处理
        const typeCheck = {
          type: message.type,
          isSystemMessage: isSystemMessage(message),
          isAIResponseChunk: isAIResponseChunk(message),
          isEvaluationUpdate: isEvaluationUpdate(message),
          isConfirmationRequest: isConfirmationRequest(message),
          isFinalPromptChunk: isFinalPromptChunk(message),
          isSessionEnd: isSessionEnd(message),
          isErrorMessage: isErrorMessage(message),
          isApiConfigResult: isApiConfigResult(message)
        };
        this.log('📋 消息分类检查', typeCheck);

        this.handleMessage(message);
      } catch (error) {
        this.log('❌ 解析 WebSocket 消息失败', error);
      }
    };
  }

  // 初始化会话
  private async initializeSession(): Promise<void> {
    // 首先发送认证信息
    await this.sendAuthentication();

    // 加载会话列表
    await this.loadSessions();
  }

  private handleMessage(message: WebSocketMessage): void {
    console.log('🎯 开始处理消息:', message.type);

    if (isAuthResult(message)) {
      console.log('🔐 进入认证结果处理分支');
      this.handleAuthResult(message.payload);
    } else if (isSystemMessage(message)) {
      console.log('📝 进入系统消息处理分支');
      this.handleSystemMessage(message.payload.message);
    } else if (isAIResponseChunk(message)) {
      console.log('🤖 进入AI响应块处理分支');
      this.handleAIResponseChunk(message.payload.chunk);
    } else if (isEvaluationUpdate(message)) {
      console.log('🔬 进入评估更新处理分支');
      this.handleEvaluationUpdate(message.payload);
    } else if (isConfirmationRequest(message)) {
      console.log('❓ 进入确认请求处理分支');
      this.handleConfirmationRequest(message.payload.reason);
    } else if (isFinalPromptChunk(message)) {
      console.log('✨ 进入最终提示块处理分支');
      this.handleFinalPromptChunk(message.payload.chunk);
    } else if (isSessionEnd(message)) {
      console.log('🔚 进入会话结束处理分支');
      this.handleSessionEnd();
    } else if (isErrorMessage(message)) {
      console.log('❌ 进入错误消息处理分支');
      this.handleError(message.payload.message);
    } else if (isApiConfigResult(message)) {
      console.log('⚙️ 进入API配置结果处理分支');
      this.handleApiConfigResult(message.payload);
    } else {
      console.warn('⚠️ 未知消息类型:', message.type);
    }

    console.log('✅ 消息处理完成');
  }

  private handleSystemMessage(message: string): void {
    console.log('📝 系统消息:', message);

    // 只有真正的系统提示才添加到聊天记录，跳过所有技术标识
    if (this.isValidChatSystemMessage(message)) {
      const chatMessage: ChatMessage = {
        id: this.generateId(),
        type: 'system',
        content: message,
        timestamp: new Date(),
        isComplete: true
      };
      this.chatMessages.value.push(chatMessage);
      console.log('✅ 添加系统消息到聊天记录');
    } else {
      console.log('🚫 跳过技术性系统消息');
    }
  }

  private isValidChatSystemMessage(message: string): boolean {
    const skipPatterns = [
      'AI:',
      'You:',
      '---',
      'None',
      /^\s*$/,
      /^[:\-=_\s]*$/
    ];

    const content = message.trim();

    for (const pattern of skipPatterns) {
      if (typeof pattern === 'string') {
        if (content === pattern || content.includes(pattern)) {
          return false;
        }
      } else if (pattern instanceof RegExp) {
        if (pattern.test(content)) {
          return false;
        }
      }
    }

    return true;
  }

  private handleAIResponseChunk(chunk: string): void {
    this.log('🤖 AI响应块详细信息', {
      chunk: chunk,
      chunkLength: chunk.length,
      hasNewlines: chunk.includes('\n'),
      hasDashes: chunk.includes('---'),
      hasNone: chunk.includes('None'),
      currentAIMessageExists: !!this.currentAIMessage.value
    });

    if (!this.currentAIMessage.value) {
      // 创建新的 AI 消息
      this.currentAIMessage.value = {
        id: this.generateId(),
        type: 'ai',
        content: chunk,
        timestamp: new Date(),
        isComplete: false
      };
      this.chatMessages.value.push(this.currentAIMessage.value);
      this.log('✅ 创建新的AI消息', { id: this.currentAIMessage.value.id });
    } else {
      // 追加到现有消息
      const oldContent = this.currentAIMessage.value.content;
      this.currentAIMessage.value.content += chunk;
      this.log('➕ 追加到现有AI消息', {
        messageId: this.currentAIMessage.value.id,
        oldContentLength: oldContent.length,
        newContentLength: this.currentAIMessage.value.content.length,
        appendedChunk: chunk
      });
    }
  }  private handleEvaluationUpdate(payload: {
    message: string;
    extracted_traits?: string[];
    extracted_keywords?: string[];
    evaluation_score?: number;
    completeness_breakdown?: {
      core_identity: number;
      personality_traits: number;
      behavioral_patterns: number;
      interaction_patterns: number;
    };
    suggestions?: string[];
    is_ready?: boolean;
  }): void {
    this.log('🔬 评估更新详细信息', {
      message: payload.message,
      extractedTraits: payload.extracted_traits,
      extractedKeywords: payload.extracted_keywords,
      evaluationScore: payload.evaluation_score,
      completenessBreakdown: payload.completeness_breakdown,
      suggestions: payload.suggestions,
      isReady: payload.is_ready,
      currentAIMessageExists: !!this.currentAIMessage.value,
      currentAIMessageContent: this.currentAIMessage.value?.content || null
    });

    // 完成当前 AI 消息
    if (this.currentAIMessage.value) {
      this.currentAIMessage.value.isComplete = true;
      this.log('🏁 完成AI消息，最终内容', this.currentAIMessage.value.content);
      this.currentAIMessage.value = null;
    }

    // 更新评估状态
    this.evaluationStatus.value = payload.message;

    // 更新提取的特征（如果有）
    if (payload.extracted_traits && payload.extracted_traits.length > 0) {
      this.extractedTraits.value = payload.extracted_traits;
      this.log('🏷️ 更新提取的特征', payload.extracted_traits);
    }

    // 更新提取的关键词
    if (payload.extracted_keywords && payload.extracted_keywords.length > 0) {
      this.extractedKeywords.value = payload.extracted_keywords;
      this.log('🔖 更新提取的关键词', payload.extracted_keywords);
    }

    // 更新评估分数
    if (payload.evaluation_score !== undefined) {
      this.evaluationScore.value = payload.evaluation_score;
      this.log('📊 更新评估分数', payload.evaluation_score);
    }

    // 更新完整度分解数据
    if (payload.completeness_breakdown) {
      this.completenessData.value = payload.completeness_breakdown;
      this.log('📈 更新完整度数据', payload.completeness_breakdown);
    }

    // 更新改进建议
    if (payload.suggestions && payload.suggestions.length > 0) {
      this.evaluationSuggestions.value = payload.suggestions;
      this.log('💡 更新改进建议', payload.suggestions);
    }

    // 控制评估卡片显示
    const hasExtractedContent = (this.extractedTraits.value.length > 0) ||
                               (this.extractedKeywords.value.length > 0) ||
                               (this.evaluationScore.value !== null);

    if (hasExtractedContent) {
      // 如果有提取的内容，不显示进度卡片
      this.showEvaluationCard.value = false;
    } else {
      // 如果是评估过程中的状态更新，显示评估卡片
      this.showEvaluationCard.value = true;

      // 3秒后自动隐藏评估卡片（仅当没有提取到内容时）
      setTimeout(() => {
        if (!hasExtractedContent) {
          this.showEvaluationCard.value = false;
        }
        this.log('⏰ 评估卡片处理完成');
      }, 3000);
    }

    // 更新当前会话的评估数据
    void this.updateCurrentSession();

    this.log('📊 更新评估状态完成', payload.message);
  }

  private handleConfirmationRequest(reason: string): void {
    console.log('❓ 确认请求:', reason);

    // 完成当前 AI 消息
    if (this.currentAIMessage.value) {
      this.currentAIMessage.value.isComplete = true;
      this.currentAIMessage.value = null;
    }

    this.pendingConfirmation.value = reason;
    this.appState.value = 'awaiting_confirmation';
  }

  private handleFinalPromptChunk(chunk: string): void {
    console.log('✨ 最终提示块:', chunk);

    this.finalPromptContent.value += chunk;

    // 不添加到聊天记录，只在右侧面板显示
  }

  private handleSessionEnd(): void {
    console.log('🔚 会话结束');

    this.appState.value = 'completed';
    this.promptTimestamp.value = new Date();
    this.showPromptResult.value = true;

    // 保存最终状态到当前会话
    void this.updateCurrentSession();

    // 延迟关闭连接
    setTimeout(() => {
      this.disconnect();
    }, 2000);
  }

  private handleError(message: string): void {
    console.log('❌ 错误:', message);

    this.appState.value = 'error';

    const chatMessage: ChatMessage = {
      id: this.generateId(),
      type: 'error',
      content: `错误: ${message}`,
      timestamp: new Date(),
      isComplete: true
    };
    this.chatMessages.value.push(chatMessage);
  }

  private scheduleReconnect(): void {
    this.reconnectAttempts++;
    setTimeout(() => {
      console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.connect();
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  private generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Session恢复相关方法
  private saveSessionId(sessionId: string): void {
    this.currentSessionId.value = sessionId;
    localStorage.setItem('easy_prompt_session_id', sessionId);
    this.log('💾 保存session ID', sessionId);
  }

  private loadSessionId(): string | null {
    const savedSessionId = localStorage.getItem('easy_prompt_session_id');
    this.log('📂 加载session ID', savedSessionId);
    return savedSessionId;
  }

  private clearSessionId(): void {
    this.currentSessionId.value = null;
    localStorage.removeItem('easy_prompt_session_id');
    this.log('🗑️ 清除session ID');
  }

  private isSessionRestored(): boolean {
    return this.sessionRestored.value;
  }

  private markSessionRestored(): void {
    this.sessionRestored.value = true;
    this.log('✅ 标记session已恢复');
  }

  // 公共方法：发送用户消息
  sendUserResponse(answer: string): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    console.log('📤 准备发送用户消息:', answer);
    console.log('🔄 当前AI消息状态:', {
      exists: !!this.currentAIMessage.value,
      content: this.currentAIMessage.value?.content || null,
      isComplete: this.currentAIMessage.value?.isComplete || null
    });

    // 完成当前的 AI 消息（如果存在）
    if (this.currentAIMessage.value) {
      this.currentAIMessage.value.isComplete = true;
      this.currentAIMessage.value = null;
      console.log('🔄 完成并清理当前AI消息状态');
    }

    const message: UserResponse = {
      type: 'user_response',
      payload: { answer }
    };

    console.log('📤 发送用户消息JSON:', JSON.stringify(message, null, 2));

    // 添加用户消息到聊天记录
    const chatMessage: ChatMessage = {
      id: this.generateId(),
      type: 'user',
      content: answer,
      timestamp: new Date(),
      isComplete: true
    };
    this.chatMessages.value.push(chatMessage);
    console.log('✅ 用户消息已添加到聊天记录, ID:', chatMessage.id);

    this.ws.send(JSON.stringify(message));
    console.log('📡 消息已通过WebSocket发送');
  }

  // 公共方法：发送确认响应
  sendConfirmation(confirm: boolean): void {
    if (this.ws?.readyState !== WebSocket.OPEN) {
      console.error('WebSocket is not connected');
      return;
    }

    // 完成当前的 AI 消息（如果存在）
    if (this.currentAIMessage.value) {
      this.currentAIMessage.value.isComplete = true;
      this.currentAIMessage.value = null;
      console.log('🔄 完成并清理当前AI消息状态');
    }

    const message: UserConfirmation = {
      type: 'user_confirmation',
      payload: { confirm }
    };

    console.log('📤 发送确认响应:', message);

    this.pendingConfirmation.value = '';
    this.appState.value = confirm ? 'generating_final_prompt' : 'chatting';

    this.ws.send(JSON.stringify(message));
  }

  // 重置所有状态
  reset(): void {
    this.chatMessages.value = [];
    this.evaluationStatus.value = '';
    this.showEvaluationCard.value = false;
    this.extractedTraits.value = [];
    this.extractedKeywords.value = [];
    this.evaluationScore.value = null;
    this.completenessData.value = {
      core_identity: 0,
      personality_traits: 0,
      behavioral_patterns: 0,
      interaction_patterns: 0
    };
    this.evaluationSuggestions.value = [];
    this.finalPromptContent.value = '';
    this.showPromptResult.value = false;
    this.promptTimestamp.value = new Date();
    this.pendingConfirmation.value = '';
    this.currentAIMessage.value = null;
    this.currentFinalPrompt.value = null;
    this.appState.value = 'initial';
  }

  // 处理API配置结果
  private handleApiConfigResult(payload: { success: boolean; message: string }): void {
    console.log('⚙️ API配置结果:', payload);

    if (payload.success) {
      this.apiConfigured.value = true;
      this.appState.value = 'chatting';
    } else {
      this.apiConfigured.value = false;
      this.appState.value = 'error';
    }

    // 可以通过事件或回调通知UI组件
    this.log('API配置结果', payload);
  }

  // 公共方法：重新配置API
  public reconfigureApi(config: ApiConfig): void {
    this.setApiConfig(config);
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.sendApiConfig();
    }
  }

  // 公共方法：获取API配置状态
  public getApiConfigStatus(): { configured: boolean; config: ApiConfig | null; complete: boolean } {
    const config = this.apiConfig.value;
    const complete = config ? this.isConfigComplete(config) : false;
    return {
      configured: this.apiConfigured.value,
      config: config,
      complete: complete
    };
  }

  // Session管理相关方法
  async getSessions(): Promise<Session[]> {
    try {
      const sessions = await apiService.getAllSessions();
      this.sessions.value = sessions;
      return sessions;
    } catch (error) {
      this.log('❌ 获取会话列表失败', error);
      return this.sessions.value;
    }
  }

  getCurrentSessionId(): string | null {
    return this.currentSessionId.value;
  }

  async createNewSession(): Promise<void> {
    try {
      const now = new Date();
      const sessionName = `会话 ${this.formatDate(now)} ${this.formatTime(now)}`;

      // 重置所有评估状态
      this.evaluationStatus.value = '';
      this.showEvaluationCard.value = false;
      this.extractedTraits.value = [];
      this.extractedKeywords.value = [];
      this.evaluationScore.value = null;
      this.completenessData.value = {
        core_identity: 0,
        personality_traits: 0,
        behavioral_patterns: 0,
        interaction_patterns: 0
      };
      this.evaluationSuggestions.value = [];
      this.finalPromptContent.value = '';
      this.showPromptResult.value = false;
      this.promptTimestamp.value = new Date();
      this.chatMessages.value = [];
      this.pendingConfirmation.value = '';
      this.currentAIMessage.value = null;
      this.currentFinalPrompt.value = null;
      this.appState.value = 'initial';

      const newSession = await apiService.createSession({
        name: sessionName
      });

      this.sessions.value.unshift(newSession);
      this.currentSessionId.value = newSession.id;
      this.log('🆕 创建新会话', newSession);
    } catch (error) {
      this.log('❌ 创建会话失败', error);
    }
  }

  async switchToSession(sessionId: string): Promise<void> {
    try {
      const session = await apiService.getSession(sessionId);
      this.currentSessionId.value = sessionId;
      this.chatMessages.value = session.messages || [];

      // 恢复评估数据
      if (session.evaluationData) {
        this.evaluationStatus.value = session.evaluationData.evaluationStatus || '';
        this.showEvaluationCard.value = session.evaluationData.showEvaluationCard || false;
        this.extractedTraits.value = session.evaluationData.extractedTraits || [];
        this.extractedKeywords.value = session.evaluationData.extractedKeywords || [];
        this.evaluationScore.value = session.evaluationData.evaluationScore || null;
        this.completenessData.value = session.evaluationData.completenessData || {
          core_identity: 0,
          personality_traits: 0,
          behavioral_patterns: 0,
          interaction_patterns: 0
        };
        this.evaluationSuggestions.value = session.evaluationData.evaluationSuggestions || [];
        this.finalPromptContent.value = session.evaluationData.finalPromptContent || '';
        this.showPromptResult.value = session.evaluationData.showPromptResult || false;
        this.promptTimestamp.value = session.evaluationData.promptTimestamp ? new Date(session.evaluationData.promptTimestamp) : new Date();

        this.log('🔄 恢复评估数据', {
          evaluationStatus: this.evaluationStatus.value,
          showEvaluationCard: this.showEvaluationCard.value,
          extractedTraits: this.extractedTraits.value,
          extractedKeywords: this.extractedKeywords.value,
          evaluationScore: this.evaluationScore.value,
          completenessData: this.completenessData.value,
          showPromptResult: this.showPromptResult.value
        });
      } else {
        // 如果没有评估数据，清空相关状态
        this.evaluationStatus.value = '';
        this.showEvaluationCard.value = false;
        this.extractedTraits.value = [];
        this.extractedKeywords.value = [];
        this.evaluationScore.value = null;
        this.completenessData.value = {
          core_identity: 0,
          personality_traits: 0,
          behavioral_patterns: 0,
          interaction_patterns: 0
        };
        this.evaluationSuggestions.value = [];
        this.finalPromptContent.value = '';
        this.showPromptResult.value = false;
        this.promptTimestamp.value = new Date();
      }

      this.log('🔄 切换到会话', session);
    } catch (error) {
      this.log('❌ 切换会话失败', error);
    }
  }

  async deleteSession(sessionId: string): Promise<void> {
    try {
      await apiService.deleteSession(sessionId);
      const index = this.sessions.value.findIndex(s => s.id === sessionId);
      if (index > -1) {
        this.sessions.value.splice(index, 1);
        this.log('🗑️ 删除会话', sessionId);

        // 如果删除的是当前会话，重置状态
        if (this.currentSessionId.value === sessionId) {
          this.reset();
        }
      }
    } catch (error) {
      this.log('❌ 删除会话失败', error);
    }
  }

  private async saveSessions(): Promise<void> {
    // 现在使用API保存，不再使用localStorage
    try {
      await this.getSessions();
    } catch (error) {
      this.log('❌ 保存会话失败', error);
    }
  }

  private async loadSessions(): Promise<void> {
    try {
      await this.getSessions();
      this.log('📂 加载会话列表', this.sessions.value);
    } catch (error) {
      this.log('❌ 加载会话失败', error);
      this.sessions.value = [];
    }
  }

  private async updateCurrentSession(): Promise<void> {
    if (this.currentSessionId.value) {
      try {
        // 更新消息
        const lastMessage = this.chatMessages.value[this.chatMessages.value.length - 1];
        if (lastMessage) {
          await apiService.addMessageToSession(this.currentSessionId.value, lastMessage);
        }

        // 更新评估数据
        const evaluationData = {
          evaluationStatus: this.evaluationStatus.value,
          showEvaluationCard: this.showEvaluationCard.value,
          extractedTraits: this.extractedTraits.value,
          extractedKeywords: this.extractedKeywords.value,
          evaluationScore: this.evaluationScore.value,
          completenessData: this.completenessData.value,
          evaluationSuggestions: this.evaluationSuggestions.value,
          finalPromptContent: this.finalPromptContent.value,
          showPromptResult: this.showPromptResult.value,
          promptTimestamp: this.promptTimestamp.value
        };

        await apiService.updateSessionEvaluation(this.currentSessionId.value, evaluationData);
      } catch (error) {
        this.log('❌ 更新会话失败', error);
      }
    }
  }

  private formatDate(date: Date): string {
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  }

  private formatTime(date: Date): string {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }

}

export const websocketService = new WebSocketService();
