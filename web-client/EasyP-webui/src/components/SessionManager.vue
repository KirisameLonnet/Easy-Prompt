<template>
  <q-dialog :model-value="show" @update:model-value="$emit('close')" maximized>
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">
          <q-icon name="folder" class="q-mr-sm" />
          会话管理器
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section class="q-pt-none">
        <div class="row q-gutter-md">
          <!-- 会话列表 -->
          <div class="col-8">
            <div class="text-subtitle2 q-mb-md">
              <q-icon name="history" class="q-mr-sm" />
              会话历史
            </div>

            <q-list bordered separator>
              <q-item
                v-for="session in sessions"
                :key="session.id"
                clickable
                v-ripple
                :class="{ 'bg-blue-1': session.id === currentSessionId }"
                @click="selectSession(session)"
              >
                <q-item-section avatar>
                  <q-avatar color="primary" text-color="white" icon="chat" />
                </q-item-section>

                <q-item-section>
                  <q-item-label>{{ session.name }}</q-item-label>
                  <q-item-label caption>
                    {{ formatDate(session.createdAt) }} - {{ formatTime(session.createdAt) }}
                  </q-item-label>
                  <q-item-label caption>
                    消息数: {{ session.messageCount }} |
                    状态: {{ getSessionStatus(session) }}
                  </q-item-label>
                </q-item-section>

                <q-item-section side>
                  <div class="row q-gutter-xs">
                    <q-btn
                      flat
                      round
                      dense
                      icon="visibility"
                      size="sm"
                      @click.stop="previewSession(session)"
                      title="预览"
                    />
                    <q-btn
                      flat
                      round
                      dense
                      icon="delete"
                      size="sm"
                      color="negative"
                      @click.stop="deleteSession(session)"
                      title="删除"
                    />
                  </div>
                </q-item-section>
              </q-item>
            </q-list>

            <div v-if="sessions.length === 0" class="text-center q-pa-lg text-grey-5">
              <q-icon name="inbox" size="3rem" class="q-mb-md" />
              <div>暂无会话记录</div>
            </div>
          </div>

          <!-- 会话详情 -->
          <div class="col-4">
            <div class="text-subtitle2 q-mb-md">
              <q-icon name="info" class="q-mr-sm" />
              会话详情
            </div>

            <q-card v-if="selectedSession" flat bordered>
              <q-card-section>
                <div class="text-h6">{{ selectedSession.name }}</div>
                <div class="text-caption text-grey-6 q-mb-md">
                  创建时间: {{ formatDateTime(selectedSession.createdAt) }}
                </div>

                <div class="q-mb-sm">
                  <q-chip size="sm" color="primary" text-color="white">
                    消息数: {{ selectedSession.messageCount }}
                  </q-chip>
                  <q-chip size="sm" :color="getStatusColor(selectedSession)" text-color="white">
                    {{ getSessionStatus(selectedSession) }}
                  </q-chip>
                </div>

                <div v-if="selectedSession.lastMessage" class="q-mt-md">
                  <div class="text-caption text-grey-7">最后消息:</div>
                  <div class="text-body2 q-mt-xs">{{ selectedSession.lastMessage }}</div>
                </div>

                <div class="q-mt-md">
                  <q-btn
                    unelevated
                    color="primary"
                    label="切换到此会话"
                    icon="swap_horiz"
                    @click="switchToSession(selectedSession)"
                    :disable="selectedSession.id === currentSessionId"
                    class="full-width"
                  />
                </div>
              </q-card-section>
            </q-card>

            <div v-else class="text-center q-pa-lg text-grey-5">
              <q-icon name="info" size="2rem" class="q-mb-md" />
              <div>选择一个会话查看详情</div>
            </div>
          </div>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat label="新建会话" icon="add" color="primary" @click="createNewSession" />
        <q-btn flat label="关闭" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>

  <!-- 会话预览对话框 -->
  <q-dialog v-model="showPreview" maximized>
    <q-card>
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">
          <q-icon name="preview" class="q-mr-sm" />
          会话预览 - {{ previewSessionData?.name }}
        </div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-scroll-area style="height: 70vh">
          <div v-if="previewSessionData" class="q-pa-md">
            <div
              v-for="(message, index) in previewSessionData.messages"
              :key="index"
              class="q-mb-md"
            >
              <q-card flat bordered>
                <q-card-section>
                  <div class="row items-center q-mb-sm">
                    <q-icon
                      :name="getMessageIcon(message.type)"
                      :color="getMessageColor(message.type)"
                      class="q-mr-sm"
                    />
                    <span class="text-subtitle2">{{ getMessageTypeName(message.type) }}</span>
                    <q-space />
                    <span class="text-caption text-grey-6">
                      {{ formatTime(message.timestamp) }}
                    </span>
                  </div>
                  <div class="text-body2">{{ message.content }}</div>
                </q-card-section>
              </q-card>
            </div>
          </div>
        </q-scroll-area>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import type { Session, ChatMessage } from 'src/types/websocket';

interface Props {
  show: boolean;
  currentSessionId?: string;
}

interface Emits {
  (e: 'close'): void;
  (e: 'switch-session', sessionId: string): void;
  (e: 'create-session'): void;
  (e: 'delete-session', sessionId: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  currentSessionId: ''
});

const emit = defineEmits<Emits>();

const sessions = ref<Session[]>([]);
const selectedSession = ref<Session | null>(null);
const showPreview = ref(false);
const previewSessionData = ref<Session | null>(null);

// 计算属性
const currentSessionId = computed(() => props.currentSessionId);

// 方法
const loadSessions = (): void => {
  const savedSessions = localStorage.getItem('easy_prompt_sessions');
  if (savedSessions) {
    try {
      const parsedSessions = JSON.parse(savedSessions);
      sessions.value = parsedSessions.map((session: Session) => ({
        ...session,
        createdAt: new Date(session.createdAt),
        messages: session.messages?.map((msg: ChatMessage) => ({
          ...msg,
          timestamp: new Date(msg.timestamp)
        })) || []
      }));
    } catch (error) {
      console.error('加载会话失败:', error);
      sessions.value = [];
    }
  }
};

const saveSessions = (): void => {
  localStorage.setItem('easy_prompt_sessions', JSON.stringify(sessions.value));
};

const createNewSession = (): void => {
  const now = new Date();
  const sessionId = `session_${now.getTime()}`;
  const sessionName = `会话 ${formatDate(now)} ${formatTime(now)}`;

  const newSession: Session = {
    id: sessionId,
    name: sessionName,
    createdAt: now,
    messageCount: 0,
    status: 'active',
    messages: []
  };

  sessions.value.unshift(newSession);
  saveSessions();
  emit('create-session');
  emit('close');
};

const selectSession = (session: Session): void => {
  selectedSession.value = session;
};

const switchToSession = (session: Session): void => {
  emit('switch-session', session.id);
  emit('close');
};

const deleteSession = (session: Session): void => {
  const index = sessions.value.findIndex(s => s.id === session.id);
  if (index > -1) {
    sessions.value.splice(index, 1);
    saveSessions();

    if (selectedSession.value?.id === session.id) {
      selectedSession.value = null;
    }

    emit('delete-session', session.id);
  }
};

const previewSession = (session: Session): void => {
  previewSessionData.value = session;
  showPreview.value = true;
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
};

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit'
  });
};

const formatDateTime = (date: Date): string => {
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getSessionStatus = (session: Session): string => {
  const statusMap = {
    'active': '进行中',
    'completed': '已完成',
    'paused': '已暂停'
  };
  return statusMap[session.status] || '未知';
};

const getStatusColor = (session: Session): string => {
  const colorMap = {
    'active': 'positive',
    'completed': 'info',
    'paused': 'warning'
  };
  return colorMap[session.status] || 'grey';
};

const getMessageIcon = (type: string): string => {
  const iconMap = {
    'user': 'person',
    'ai': 'smart_toy',
    'system': 'settings',
    'error': 'error'
  };
  return iconMap[type] || 'chat';
};

const getMessageColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    'user': 'primary',
    'ai': 'secondary',
    'system': 'info',
    'error': 'negative'
  };
  return colorMap[type] || 'grey';
};

const getMessageTypeName = (type: string): string => {
  const nameMap: Record<string, string> = {
    'user': '用户',
    'ai': 'AI助手',
    'system': '系统',
    'error': '错误'
  };
  return nameMap[type] || '未知';
};

// 生命周期
onMounted(() => {
  loadSessions();
});
</script>

<style scoped lang="scss">
.q-item {
  transition: all 0.2s ease;

  &:hover {
    background-color: rgba(0, 0, 0, 0.04);
  }
}

.q-chip {
  margin: 2px;
}
</style>
