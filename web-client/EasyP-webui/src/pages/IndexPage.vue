<template>
  <q-page class="chat-page">
    <!-- 主容器 - 包含侧边栏和内容 -->
    <div class="page-container">
      <!-- ChatGPT风格的侧边栏 -->
      <SessionSidebar
        :current-session-id="currentSessionId || ''"
        @session-changed="handleSessionChanged"
      />

      <!-- 主内容区域 -->
      <div class="main-content">
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
              icon="settings"
              @click="showApiConfig = true"
              title="API配置"
              :color="apiConfigComplete ? 'positive' : 'warning'"
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

    <!-- 主要内容区域 - 使用 Quasar Splitter 实现响应式布局 -->
    <q-splitter
      v-model="splitterModel"
      :limits="splitterLimits"
      :horizontal="isMobile"
      class="main-content-splitter"
    >
      <!-- 对话区域 -->
      <template v-slot:before>
        <q-card class="chat-card fit" flat bordered>
          <q-card-section class="chat-card-header bg-grey-1 q-pa-md">
            <div class="row items-center no-wrap">
              <q-icon name="chat" size="sm" class="q-mr-sm" />
              <div class="col">
                <div class="text-subtitle1 text-grey-8">对话区域</div>
                <div class="text-caption text-grey-6">与 AI 助手进行角色设定对话</div>
              </div>
            </div>
          </q-card-section>

          <q-separator />

          <!-- 聊天消息区域 -->
          <q-card-section class="chat-messages-container q-pa-none">
            <q-scroll-area
              ref="scrollArea"
              class="chat-messages"
              :style="{ height: chatHeight }"
            >
              <div class="messages-list q-pa-md">
                <!-- 配置提示消息 -->
                <q-banner
                  v-if="!apiConfigComplete"
                  class="bg-orange-1 text-orange-9 q-mb-md"
                  rounded
                  dense
                >
                  <template v-slot:avatar>
                    <q-icon name="settings" color="warning" />
                  </template>
                  <div class="text-subtitle2 q-mb-xs">需要配置API</div>
                  <div class="text-caption">请先点击右上角的设置按钮配置API密钥和模型信息</div>
                  <template v-slot:action>
                    <q-btn
                      flat
                      dense
                      color="warning"
                      label="立即配置"
                      @click="showApiConfig = true"
                    />
                  </template>
                </q-banner>

                <!-- 消息列表 -->
                <ChatMessage
                  v-for="message in filteredChatMessages"
                  :key="message.id"
                  :message="message"
                />
              </div>
            </q-scroll-area>
          </q-card-section>

          <q-separator />

          <!-- 输入区域 -->
          <q-card-section class="chat-input-section q-pa-md">
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
      </template>

      <!-- 评估状态区域 -->
      <template v-slot:after>
        <div class="evaluation-section">
          <EnhancedEvaluationCard
            class="evaluation-panel"
            :evaluation-status="evaluationStatus"
            :show-evaluation-card="showEvaluationCard"
            :extracted-traits="extractedTraits"
            :extracted-keywords="extractedKeywords"
            :evaluation-score="evaluationScore"
            :completeness-data="completenessData"
            @re-evaluate="handleReEvaluate"
            @trait-selected="handleTraitSelected"
            @generate-prompt="handleGeneratePrompt"
          />
        </div>
      </template>
        </q-splitter>
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
              <li>在对话区与 AI 讨论角色设定</li>
              <li>右侧会实时显示评估状态和角色特征</li>
              <li>完成后系统会自动生成提示词</li>
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
      @continue-conversation="handleContinueConversation"
    />

    <!-- API配置对话框 -->
    <ApiConfigDialog
      v-model="showApiConfig"
      :initial-config="currentApiConfig"
      @config-saved="handleApiConfigSaved"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import { QScrollArea, useQuasar } from 'quasar';
import ChatMessage from 'src/components/ChatMessage.vue';
import ChatInput from 'src/components/ChatInput.vue';
import PromptResult from 'src/components/PromptResult.vue';
import ApiConfigDialog from 'src/components/ApiConfigDialog.vue';
import EnhancedEvaluationCard from 'src/components/EnhancedEvaluationCard.vue';
import SessionSidebar from 'src/components/SessionSidebar.vue';
import DebugPanel from 'src/components/DebugPanel.vue';
import { websocketService, type ApiConfig } from 'src/services/websocket';
import { WEBSOCKET_URL } from 'src/config/backend';

// Quasar 实例
const $q = useQuasar();

// 响应式数据
const showInfo = ref(false)
const showDebug = ref(false);
const showApiConfig = ref(false);
const chatInput = ref<InstanceType<typeof ChatInput>>();
const scrollArea = ref<QScrollArea>();

// 检测是否为移动设备
const isMobile = computed(() => $q.screen.lt.md); // 小于 md (1024px) 时为移动设备

// Splitter 相关配置 - 根据设备类型设置默认值
const splitterModel = ref(isMobile.value ? 55 : 70); // 移动端上部占55%，桌面端左侧占70%

// Splitter 限制
const splitterLimits = computed(() => {
  if (isMobile.value) {
    // 移动设备：水平分割，上下分配
    return [45, 65];
  } else {
    // 桌面设备：垂直分割，左侧至少50%，最多85%
    return [50, 85];
  }
});

// 监听屏幕尺寸变化，自动调整 splitter
watch(isMobile, (newValue) => {
  splitterModel.value = newValue ? 55 : 70;
});

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

const apiConfigComplete = computed(() => {
  const status = websocketService.getApiConfigStatus();
  return status.complete;
});

// 移除认证状态检查

const websocketUrl = WEBSOCKET_URL;

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
const handleSessionChanged = (sessionId: string): void => {
  console.log('Session changed to:', sessionId);
  chatInput.value?.focusInput();
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

const handleGeneratePrompt = (): void => {
  // 直接调用生成提示词方法
  websocketService.generatePrompt();
};

const handleContinueConversation = (): void => {
  // 继续补充对话
  websocketService.continueConversation();
  chatInput.value?.focusInput();
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
    api_type: 'openai' as const,
    api_key: '',
    base_url: '',
    model: '',
    evaluator_model: '',
    temperature: 0.7,
    max_tokens: 4000,
    nsfw_mode: false
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
  // 直接连接WebSocket，无需认证
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

.page-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  flex-shrink: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  z-index: 20;
}

.main-content-splitter {
  flex: 1;
  height: calc(100vh - 64px); // 减去头部高度
}

.chat-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-card-header {
  flex-shrink: 0;
}

.chat-messages-container {
  flex: 1;
  overflow: hidden;
}

.chat-messages {
  height: 100%;
  background-color: white;
}

.chat-input-section {
  flex-shrink: 0;
  background-color: #fafafa;
}

.evaluation-section {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding: 8px;
}

.evaluation-panel {
  flex: 1;
  min-height: 0; // 关键：允许正确缩小
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
}

// Quasar Splitter 优化
:deep(.q-splitter__separator) {
  background-color: #e0e0e0;

  &:hover {
    background-color: #1976d2;
  }
}

:deep(.q-splitter__before),
:deep(.q-splitter__after) {
  overflow: hidden;
}

// 暗色主题支持
.body--dark {
  :deep(.q-splitter__separator) {
    background-color: #424242;

    &:hover {
      background-color: #64b5f6;
    }
  }
}
</style>
