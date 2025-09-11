<template>
  <q-page class="chat-page">
    <!-- 头部 -->
    <div class="chat-header">
      <q-toolbar class="bg-primary text-white">
        <q-toolbar-title class="text-center">
          <q-icon name="auto_awesome" class="q-mr-sm" />
          Easy Prompt - 角色扮演提示词生成器
        </q-toolbar-title>

        <q-btn
          flat
          round
          dense
          icon="folder"
          @click="showSessionManager = true"
          title="会话管理器"
        />

        <q-btn
          flat
          round
          dense
          icon="settings"
          @click="showApiConfig = true"
          title="API配置"
        />

        <q-btn
          flat
          round
          dense
          icon="bug_report"
          @click="showDebug = true"
          title="调试日志"
        />

        <q-btn
          flat
          round
          dense
          icon="info"
          @click="showInfo = true"
        />
      </q-toolbar>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：主对话区域 -->
      <div class="chat-section">
        <q-card class="chat-card full-height" flat bordered>
          <q-card-section class="chat-card-header bg-grey-1">
            <div class="text-h6 text-grey-8">
              <q-icon name="chat" class="q-mr-sm" />
              对话区域
            </div>
            <div class="text-caption text-grey-6">
              与 AI 助手进行角色设定对话
            </div>
          </q-card-section>

          <!-- 聊天消息区域 -->
          <q-card-section class="chat-messages-container">
            <q-scroll-area
              ref="scrollArea"
              class="chat-messages"
              :style="{ height: chatHeight }"
            >
              <div class="messages-list q-pa-md">
                <!-- 欢迎消息 -->
                <div v-if="chatMessages.length === 0" class="welcome-message">
                  <q-card class="welcome-card" flat bordered>
                    <q-card-section class="text-center">
                      <q-icon name="waving_hand" size="2rem" color="primary" class="q-mb-md" />
                      <div class="text-h6 q-mb-md">开始创建你的角色</div>
                      <div class="text-body2 text-grey-7">
                        请描述你想要的角色特征，我将帮助你完善角色设定...
                      </div>
                    </q-card-section>
                  </q-card>
                </div>

                <!-- 消息列表 -->
                <ChatMessage
                  v-for="message in filteredChatMessages"
                  :key="message.id"
                  :message="message"
                />
              </div>
            </q-scroll-area>
          </q-card-section>

          <!-- 输入区域 -->
          <q-card-section class="chat-input-section">
            <ChatInput
              ref="chatInput"
              :connection-status="connectionStatus"
              :app-state="appState"
              :messages="chatMessages"
              :confirmation-reason="pendingConfirmation"
              :loading="isLoading"
              @send-message="handleSendMessage"
              @send-confirmation="handleSendConfirmation"
              @reconnect="reconnect"
              @clear="handleClear"
            />
          </q-card-section>
        </q-card>
      </div>

      <!-- 右侧：状态和结果区域 -->
      <div class="side-panels">
        <!-- 增强评估状态卡片 -->
        <EnhancedEvaluationCard
          class="evaluation-panel"
          :evaluation-status="evaluationStatus"
          :show-evaluation-card="showEvaluationCard"
          :extracted-traits="extractedTraits"
          :extracted-keywords="extractedKeywords"
          :evaluation-score="evaluationScore"
          :completeness-data="completenessData"
          card-height="450px"
          @re-evaluate="handleReEvaluate"
          @trait-selected="handleTraitSelected"
        />

        <!-- 提示词结果卡片 -->
        <q-card
          class="result-panel"
          :class="{ 'panel-active': finalPromptContent.length > 0 }"
          flat
          bordered
        >
          <q-card-section class="panel-header bg-green-1">
            <div class="text-subtitle1 text-green-8">
              <q-icon name="auto_awesome" class="q-mr-sm" />
              提示词结果
            </div>
          </q-card-section>

          <q-card-section class="panel-content">
            <div v-if="finalPromptContent.length > 0" class="result-ready">
              <div class="result-preview">
                <q-icon name="check_circle" size="md" color="positive" class="q-mb-sm" />
                <div class="text-body2 text-positive q-mb-xs">提示词已生成</div>
                <div class="text-caption text-grey-7 q-mb-md">
                  {{ formatDate(promptTimestamp) }}
                </div>
                <q-btn
                  unelevated
                  icon="visibility"
                  label="查看完整结果"
                  color="positive"
                  size="sm"
                  @click="showPromptResult = true"
                />
              </div>
            </div>
            <div v-else class="result-waiting">
              <q-icon name="auto_awesome" size="md" color="grey-4" class="q-mb-sm" />
              <div class="text-body2 text-grey-5">等待生成结果...</div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

        <!-- 调试面板对话框 -->
    <DebugPanel v-model:show="showDebug" />

    <!-- 信息面板对话框 -->
    <q-dialog v-model="showInfo">
      <q-card style="min-width: 350px">
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">关于 Easy Prompt</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="text-body2">
            <p><strong>Easy Prompt</strong> 是一个智能的角色扮演提示词生成工具。</p>
            <p class="q-mt-md"><strong>使用方法：</strong></p>
            <ul class="q-pl-md">
              <li>在左侧对话区与 AI 讨论角色设定</li>
              <li>右侧会显示评估进度和最终结果</li>
              <li>完成后可查看和下载生成的提示词</li>
            </ul>
            <p class="q-mt-md text-caption text-grey-6">
              WebSocket 地址: {{ websocketUrl }}
            </p>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- 提示词结果展示 -->
    <PromptResult
      :show="showPromptResult"
      :content="finalPromptContent"
      :timestamp="promptTimestamp"
      @close="handleClosePromptResult"
      @new-chat="handleNewChat"
    />

    <!-- API配置对话框 -->
    <ApiConfigDialog
      v-model="showApiConfig"
      :initial-config="currentApiConfig"
      @config-saved="handleApiConfigSaved"
    />

    <!-- 会话管理器对话框 -->
    <SessionManager
      :show="showSessionManager"
      :current-session-id="currentSessionId || ''"
      @close="showSessionManager = false"
      @switch-session="handleSwitchSession"
      @create-session="handleCreateSession"
      @delete-session="handleDeleteSession"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { QScrollArea } from 'quasar';
import ChatMessage from 'src/components/ChatMessage.vue';
import ChatInput from 'src/components/ChatInput.vue';
import PromptResult from 'src/components/PromptResult.vue';
import ApiConfigDialog from 'src/components/ApiConfigDialog.vue';
import EnhancedEvaluationCard from 'src/components/EnhancedEvaluationCard.vue';
import SessionManager from 'src/components/SessionManager.vue';
import { websocketService, type ApiConfig } from 'src/services/websocket';

// 响应式数据
const showInfo = ref(false)
const showDebug = ref(false);
const showApiConfig = ref(false);
const showSessionManager = ref(false);
const chatInput = ref<InstanceType<typeof ChatInput>>();
const scrollArea = ref<QScrollArea>();

// WebSocket 状态（从服务中获取）
const connectionStatus = computed(() => websocketService.connectionStatus.value);
const appState = computed(() => websocketService.appState.value);
const chatMessages = computed(() => websocketService.chatMessages.value);
const pendingConfirmation = computed(() => websocketService.pendingConfirmation.value);
const evaluationStatus = computed(() => websocketService.evaluationStatus.value);
const showEvaluationCard = computed(() => websocketService.showEvaluationCard.value);
const extractedTraits = computed(() => websocketService.extractedTraits.value);
const extractedKeywords = computed(() => websocketService.extractedKeywords.value);
const evaluationScore = computed(() => websocketService.evaluationScore.value);
const completenessData = computed(() => websocketService.completenessData.value);
const finalPromptContent = computed(() => websocketService.finalPromptContent.value);
const showPromptResult = computed(() => websocketService.showPromptResult.value);
const promptTimestamp = computed(() => websocketService.promptTimestamp.value);
const currentSessionId = computed(() => websocketService.getCurrentSessionId());

// 计算属性
const isLoading = computed(() => {
  return appState.value === 'generating_final_prompt' ||
         connectionStatus.value === 'connecting';
});

const websocketUrl = 'ws://127.0.0.1:8000/ws/prompt';

const chatHeight = computed(() => {
  // 计算聊天区域高度
  return 'calc(100vh - 300px)';
});

// 对话消息（严格分离，只显示纯对话内容）
const filteredChatMessages = computed(() => {
  return chatMessages.value.filter(msg => {
    // 只显示用户、AI、系统和错误消息
    return ['user', 'ai', 'system', 'error'].includes(msg.type);
  });
});

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 方法
const handleSendMessage = (message: string): void => {
  websocketService.sendUserResponse(message);
  void scrollToBottom();
};

const handleSendConfirmation = (confirm: boolean): void => {
  websocketService.sendConfirmation(confirm);
  void scrollToBottom();
};

const reconnect = (): void => {
  websocketService.disconnect();
  setTimeout(() => {
    websocketService.connect();
  }, 1000);
};

const handleClear = (): void => {
  websocketService.reset();
  chatInput.value?.focusInput();
};

const handleClosePromptResult = (): void => {
  websocketService.showPromptResult.value = false;
};

const handleNewChat = (): void => {
  websocketService.reset();
  websocketService.connect();
  chatInput.value?.focusInput();
};

// 会话管理相关方法
const handleSwitchSession = (sessionId: string): void => {
  websocketService.switchToSession(sessionId);
  chatInput.value?.focusInput();
};

const handleCreateSession = (): void => {
  websocketService.createNewSession();
  websocketService.reset();
  chatInput.value?.focusInput();
};

const handleDeleteSession = (sessionId: string): void => {
  websocketService.deleteSession(sessionId);
};

// 增强评估卡片处理方法
const handleReEvaluate = (): void => {
  // 触发重新评估
  websocketService.sendUserResponse('请重新评估当前角色档案');
};

const handleTraitSelected = (trait: string): void => {
  // 处理特性选择，可以显示详细信息或进行其他操作
  console.log('选择的特性:', trait);
  // 这里可以添加更多逻辑，比如显示特性详情对话框
};

const scrollToBottom = async (): Promise<void> => {
  await nextTick();
  if (scrollArea.value) {
    const scrollTarget = scrollArea.value.getScrollTarget();
    scrollArea.value.setScrollPosition('vertical', scrollTarget.scrollHeight, 300);
  }
};

// API配置处理
const currentApiConfig = computed(() => {
  const status = websocketService.getApiConfigStatus();
  return status.config || {
    api_type: 'openai' as const,  // 默认使用OpenAI格式
    api_key: '',
    base_url: 'https://api.deepseek.com/v1',  // 默认使用DeepSeek
    model: 'deepseek-chat',  // 默认使用DeepSeek Chat模型
    temperature: 0.7,
    max_tokens: 4000,
    nsfw_mode: false // 默认值，确保类型兼容
  };
});

const handleApiConfigSaved = (config: ApiConfig): void => {
  console.log('保存API配置:', config);
  websocketService.reconfigureApi(config);
  showApiConfig.value = false;

  // 如果连接已经建立，重新连接以应用新配置
  if (websocketService.connectionStatus.value === 'connected') {
    reconnect();
  }
};

// 监听消息变化，自动滚动到底部
watch(chatMessages, () => {
  void scrollToBottom();
}, { deep: true });

// 生命周期
onMounted(() => {
  websocketService.connect();

  // 延迟聚焦输入框
  setTimeout(() => {
    chatInput.value?.focusInput();
  }, 500);
});

onUnmounted(() => {
  websocketService.disconnect();
});
</script>

<style scoped lang="scss">
.chat-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background-color: #f5f5f5;
}

.chat-header {
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 20;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.chat-section {
  flex: 1;
  min-width: 0; // 防止 flex 项目过度扩展
}

.chat-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-card-header {
  flex-shrink: 0;
  border-bottom: 1px solid #e0e0e0;
}

.chat-messages-container {
  flex: 1;
  overflow: hidden;
  padding: 0;
}

.chat-messages {
  height: 100%;
  background-color: white;
}

.chat-input-section {
  flex-shrink: 0;
  border-top: 1px solid #e0e0e0;
  background-color: #fafafa;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
}

.welcome-message {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;

  .welcome-card {
    max-width: 400px;
    border: 2px dashed #e0e0e0;
    background: linear-gradient(45deg, #f9f9f9 25%, transparent 25%),
                linear-gradient(-45deg, #f9f9f9 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #f9f9f9 75%),
                linear-gradient(-45deg, transparent 75%, #f9f9f9 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
  }
}

.side-panels {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
}

.evaluation-panel,
.result-panel {
  flex: 1;
  min-height: 200px;
  transition: all 0.3s ease;
  opacity: 0.7;

  &.panel-active {
    opacity: 1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

.panel-header {
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.panel-content {
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: 120px;
}

.evaluation-active,
.evaluation-waiting,
.traits-display,
.result-ready,
.result-waiting {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.evaluation-status,
.traits-display {
  max-width: 200px;
}

.traits-list {
  max-width: 250px;
  text-align: center;
}

.result-preview {
  max-width: 200px;
}

// 响应式设计
@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
    gap: 12px;
  }

  .side-panels {
    width: 100%;
    flex-direction: row;
    min-height: auto;
  }

  .evaluation-panel,
  .result-panel {
    flex: 1;
    min-height: 150px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 8px;
  }

  .side-panels {
    flex-direction: column;
  }

  .evaluation-panel,
  .result-panel {
    min-height: 120px;
  }

  .chat-header {
    .q-toolbar-title {
      font-size: 1rem;
    }
  }
}
</style>
