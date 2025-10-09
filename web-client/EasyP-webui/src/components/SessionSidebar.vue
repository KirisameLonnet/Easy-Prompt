<template>
  <div
    class="session-sidebar"
    :class="{ 'collapsed': collapsed }"
  >
    <!-- 侧边栏头部 -->
    <div class="sidebar-header" :class="{ 'collapsed': collapsed }">
      <q-btn
        v-if="!collapsed"
        unelevated
        color="primary"
        icon="add"
        label="新建会话"
        class="new-chat-btn"
        @click="createNewSession"
      />
      <q-btn
        v-else
        unelevated
        color="primary"
        icon="add"
        round
        class="new-chat-btn-collapsed"
        @click="createNewSession"
      >
        <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
          新建会话
        </q-tooltip>
      </q-btn>

      <q-btn
        flat
        round
        dense
        :icon="collapsed ? 'arrow_forward_ios' : 'arrow_back_ios'"
        class="collapse-btn"
        @click="toggleCollapse"
      >
        <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
          {{ collapsed ? '展开侧边栏' : '折叠侧边栏' }}
        </q-tooltip>
      </q-btn>
    </div>

    <!-- 搜索框 -->
    <div v-if="!collapsed" class="search-box">
      <q-input
        v-model="searchQuery"
        dense
        outlined
        placeholder="搜索会话..."
        bg-color="grey-2"
      >
        <template v-slot:prepend>
          <q-icon name="search" />
        </template>
        <template v-slot:append v-if="searchQuery">
          <q-icon name="close" class="cursor-pointer" @click="searchQuery = ''" />
        </template>
      </q-input>
    </div>

    <!-- 会话列表 -->
    <q-scroll-area class="session-list" :class="{ 'collapsed': collapsed }">
      <div v-if="!collapsed">
        <!-- 今天 -->
        <div v-if="todaySessions.length > 0" class="session-group">
          <div class="group-title">今天</div>
          <SessionItem
            v-for="session in todaySessions"
            :key="session.id"
            :session="session"
            :is-active="session.id === currentSessionId"
            @click="switchSession(session.id)"
            @rename="renameSession"
            @delete="confirmDeleteSession"
          />
        </div>

        <!-- 昨天 -->
        <div v-if="yesterdaySessions.length > 0" class="session-group">
          <div class="group-title">昨天</div>
          <SessionItem
            v-for="session in yesterdaySessions"
            :key="session.id"
            :session="session"
            :is-active="session.id === currentSessionId"
            @click="switchSession(session.id)"
            @rename="renameSession"
            @delete="confirmDeleteSession"
          />
        </div>

        <!-- 过去7天 -->
        <div v-if="past7DaysSessions.length > 0" class="session-group">
          <div class="group-title">过去7天</div>
          <SessionItem
            v-for="session in past7DaysSessions"
            :key="session.id"
            :session="session"
            :is-active="session.id === currentSessionId"
            @click="switchSession(session.id)"
            @rename="renameSession"
            @delete="confirmDeleteSession"
          />
        </div>

        <!-- 过去30天 -->
        <div v-if="past30DaysSessions.length > 0" class="session-group">
          <div class="group-title">过去30天</div>
          <SessionItem
            v-for="session in past30DaysSessions"
            :key="session.id"
            :session="session"
            :is-active="session.id === currentSessionId"
            @click="switchSession(session.id)"
            @rename="renameSession"
            @delete="confirmDeleteSession"
          />
        </div>

        <!-- 更早 -->
        <div v-if="olderSessions.length > 0" class="session-group">
          <div class="group-title">更早</div>
          <SessionItem
            v-for="session in olderSessions"
            :key="session.id"
            :session="session"
            :is-active="session.id === currentSessionId"
            @click="switchSession(session.id)"
            @rename="renameSession"
            @delete="confirmDeleteSession"
          />
        </div>

        <!-- 空状态 -->
        <div v-if="filteredSessions.length === 0" class="empty-state">
          <q-icon name="chat_bubble_outline" size="48px" color="grey-5" />
          <div class="text-grey-6 q-mt-md">
            {{ searchQuery ? '未找到匹配的会话' : '暂无会话' }}
          </div>
        </div>
      </div>

      <!-- 折叠状态下的简化列表 -->
      <div v-else class="collapsed-list">
        <div
          v-for="session in recentSessions"
          :key="session.id"
          class="collapsed-item"
          :class="{ 'active': session.id === currentSessionId }"
          @click="switchSession(session.id)"
        >
          <q-tooltip anchor="center right" self="center left" :offset="[10, 0]">
            {{ session.name }}
          </q-tooltip>
          <q-icon name="chat" size="20px" />
        </div>
      </div>
    </q-scroll-area>

    <!-- 重命名对话框 -->
    <q-dialog v-model="showRenameDialog">
      <q-card style="min-width: 350px">
        <q-card-section>
          <div class="text-h6">重命名会话</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-input
            v-model="newSessionName"
            dense
            outlined
            autofocus
            label="会话名称"
            @keyup.enter="confirmRename"
          />
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="取消" color="grey" v-close-popup />
          <q-btn flat label="确定" color="primary" @click="confirmRename" />
        </q-card-actions>
      </q-card>
    </q-dialog>

    <!-- 删除确认对话框 -->
    <q-dialog v-model="showDeleteDialog">
      <q-card>
        <q-card-section>
          <div class="text-h6">确认删除</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          确定要删除这个会话吗？此操作无法撤销。
        </q-card-section>

        <q-card-actions align="right">
          <q-btn flat label="取消" color="grey" v-close-popup />
          <q-btn flat label="删除" color="negative" @click="confirmDelete" />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useQuasar } from 'quasar';
import SessionItem from './SessionItem.vue';
import type { Session } from 'src/types/websocket';
import { websocketService } from 'src/services/websocket';
import { apiService } from 'src/services/api';

interface Props {
  currentSessionId?: string;
}

interface Emits {
  (e: 'session-changed', sessionId: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  currentSessionId: ''
});

const emit = defineEmits<Emits>();
const $q = useQuasar();

// 状态
const collapsed = ref(false);
const searchQuery = ref('');
const sessions = ref<Session[]>([]);
const showRenameDialog = ref(false);
const showDeleteDialog = ref(false);
const renamingSessionId = ref<string | null>(null);
const deletingSessionId = ref<string | null>(null);
const newSessionName = ref('');

// 加载会话列表
const loadSessions = async () => {
  try {
    const loadedSessions = await websocketService.getSessions();
    sessions.value = loadedSessions.sort((a, b) =>
      new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    );
  } catch (error) {
    console.error('加载会话失败:', error);
    $q.notify({
      type: 'negative',
      message: '加载会话列表失败'
    });
  }
};

// 过滤后的会话
const filteredSessions = computed(() => {
  if (!searchQuery.value) {
    return sessions.value;
  }
  const query = searchQuery.value.toLowerCase();
  return sessions.value.filter(session =>
    session.name.toLowerCase().includes(query) ||
    session.lastMessage?.toLowerCase().includes(query)
  );
});

// 时间分组辅助函数
const isToday = (date: Date): boolean => {
  const today = new Date();
  return date.toDateString() === today.toDateString();
};

const isYesterday = (date: Date): boolean => {
  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  return date.toDateString() === yesterday.toDateString();
};

const isPast7Days = (date: Date): boolean => {
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  const twoDaysAgo = new Date();
  twoDaysAgo.setDate(twoDaysAgo.getDate() - 2);
  return date >= sevenDaysAgo && date < twoDaysAgo;
};

const isPast30Days = (date: Date): boolean => {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  return date >= thirtyDaysAgo && date < sevenDaysAgo;
};

// 分组会话
const todaySessions = computed(() =>
  filteredSessions.value.filter(s => isToday(new Date(s.createdAt)))
);

const yesterdaySessions = computed(() =>
  filteredSessions.value.filter(s => isYesterday(new Date(s.createdAt)))
);

const past7DaysSessions = computed(() =>
  filteredSessions.value.filter(s => isPast7Days(new Date(s.createdAt)))
);

const past30DaysSessions = computed(() =>
  filteredSessions.value.filter(s => isPast30Days(new Date(s.createdAt)))
);

const olderSessions = computed(() => {
  const thirtyDaysAgo = new Date();
  thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
  return filteredSessions.value.filter(s => new Date(s.createdAt) < thirtyDaysAgo);
});

// 折叠状态下显示最近的会话
const recentSessions = computed(() => sessions.value.slice(0, 10));

// 方法
const toggleCollapse = () => {
  collapsed.value = !collapsed.value;
  localStorage.setItem('sidebar-collapsed', collapsed.value.toString());
};

const createNewSession = async () => {
  try {
    await websocketService.createNewSession();
    await loadSessions();
    $q.notify({
      type: 'positive',
      message: '新会话已创建'
    });
  } catch (error) {
    console.error('创建会话失败:', error);
    $q.notify({
      type: 'negative',
      message: '创建会话失败'
    });
  }
};

const switchSession = async (sessionId: string) => {
  if (sessionId === props.currentSessionId) return;

  try {
    await websocketService.switchToSession(sessionId);
    emit('session-changed', sessionId);
  } catch (error) {
    console.error('切换会话失败:', error);
    $q.notify({
      type: 'negative',
      message: '切换会话失败'
    });
  }
};

const renameSession = (sessionId: string, currentName: string) => {
  renamingSessionId.value = sessionId;
  newSessionName.value = currentName;
  showRenameDialog.value = true;
};

const confirmRename = async () => {
  if (!renamingSessionId.value || !newSessionName.value.trim()) return;

  try {
    await apiService.updateSession(renamingSessionId.value, {
      name: newSessionName.value.trim()
    });
    await loadSessions();
    showRenameDialog.value = false;
    $q.notify({
      type: 'positive',
      message: '会话已重命名'
    });
  } catch (error) {
    console.error('重命名失败:', error);
    $q.notify({
      type: 'negative',
      message: '重命名失败'
    });
  }
};

const confirmDeleteSession = (sessionId: string) => {
  deletingSessionId.value = sessionId;
  showDeleteDialog.value = true;
};

const confirmDelete = async () => {
  if (!deletingSessionId.value) return;

  try {
    await websocketService.deleteSession(deletingSessionId.value);
    await loadSessions();
    showDeleteDialog.value = false;
    $q.notify({
      type: 'positive',
      message: '会话已删除'
    });
  } catch (error) {
    console.error('删除失败:', error);
    $q.notify({
      type: 'negative',
      message: '删除失败'
    });
  }
};

// 生命周期
onMounted(async () => {
  await loadSessions();

  // 恢复侧边栏折叠状态
  const savedCollapsed = localStorage.getItem('sidebar-collapsed');
  if (savedCollapsed) {
    collapsed.value = savedCollapsed === 'true';
  }
});

// 监听会话变化
watch(() => props.currentSessionId, () => {
  void loadSessions();
});
</script>

<style scoped lang="scss">
.session-sidebar {
  width: 280px;
  height: 100%;
  background-color: #f7f7f8;
  border-right: 1px solid #e5e5e5;
  display: flex;
  flex-direction: column;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);

  &.collapsed {
    width: 60px;
  }
}

.sidebar-header {
  padding: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #e5e5e5;
  background-color: #fff;

  &.collapsed {
    flex-direction: column;
    padding: 8px;

    .collapse-btn {
      margin-top: 8px;
    }
  }

  .new-chat-btn {
    flex: 1;
    font-weight: 500;
    transition: all 0.2s ease;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
    }

    &:active {
      transform: translateY(0);
    }
  }

  .new-chat-btn-collapsed {
    transition: all 0.2s ease;

    &:hover {
      transform: scale(1.1);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  .collapse-btn {
    flex-shrink: 0;
    transition: all 0.2s ease;

    &:hover {
      background-color: rgba(0, 0, 0, 0.08);
      transform: scale(1.1);
    }

    &:active {
      transform: scale(0.95);
    }

    :deep(.q-icon) {
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      font-size: 18px;
    }
  }
}

.search-box {
  padding: 12px;
  border-bottom: 1px solid #e5e5e5;
  background-color: #fff;

  :deep(.q-field__control) {
    transition: all 0.2s ease;

    &:hover {
      background-color: #f0f0f0;
    }
  }

  :deep(.q-field--focused .q-field__control) {
    box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
  }
}

.session-list {
  flex: 1;
  padding: 8px;

  &.collapsed {
    padding: 8px 4px;
  }
}

.session-group {
  margin-bottom: 16px;
  animation: fadeIn 0.3s ease;

  .group-title {
    font-size: 12px;
    font-weight: 600;
    color: #6e6e80;
    padding: 8px 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
  animation: fadeIn 0.5s ease;
}

.collapsed-list {
  display: flex;
  flex-direction: column;
  gap: 8px;

  .collapsed-item {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 40px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    color: #6e6e80;

    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }

    &.active {
      background-color: #ececf1;
      color: #10a37f;
    }
  }
}

// 暗色主题支持
.body--dark {
  .session-sidebar {
    background-color: #202123;
    border-right-color: #2a2b32;
  }

  .sidebar-header {
    border-bottom-color: #2a2b32;
    background-color: #202123;

    .collapse-btn:hover {
      background-color: rgba(255, 255, 255, 0.08);
    }
  }

  .search-box {
    border-bottom-color: #2a2b32;
    background-color: #202123;

    :deep(.q-field__control) {
      &:hover {
        background-color: #2a2b32;
      }
    }
  }

  .group-title {
    color: #8e8ea0;
  }

  .collapsed-item {
    color: #8e8ea0;

    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }

    &.active {
      background-color: #2a2b32;
      color: #10a37f;
    }
  }
}
</style>

