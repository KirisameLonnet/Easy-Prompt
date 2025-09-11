<template>
  <q-dialog :model-value="show" persistent maximized @update:model-value="$emit('update:show', $event)">
    <q-card class="debug-panel">
      <q-card-section class="debug-header">
        <div class="text-h6">WebSocket 调试日志</div>
        <q-space />
        <q-btn
          flat
          round
          dense
          icon="refresh"
          @click="refreshLogs"
          title="刷新日志"
        />
        <q-btn
          flat
          round
          dense
          icon="delete"
          @click="clearLogs"
          title="清空日志"
        />
        <q-btn
          flat
          round
          dense
          icon="close"
          @click="$emit('update:show', false)"
          title="关闭"
        />
      </q-card-section>

      <q-card-section class="debug-content">
        <q-scroll-area
          ref="scrollArea"
          class="log-container"
          :thumb-style="{ right: '4px', borderRadius: '5px', backgroundColor: '#027be3', width: '5px', opacity: '0.75' }"
        >
          <div class="log-content">
            <div
              v-for="(log, index) in logs"
              :key="index"
              :class="['log-line', getLogClass(log)]"
            >
              {{ log }}
            </div>
            <div v-if="logs.length === 0" class="no-logs">
              暂无调试日志
            </div>
          </div>
        </q-scroll-area>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { QScrollArea } from 'quasar';
import { websocketService } from 'src/services/websocket';

defineProps<{
  show: boolean;
}>();

defineEmits<{
  close: [];
  'update:show': [value: boolean];
}>();

const scrollArea = ref<QScrollArea>();
const logs = ref<string[]>([]);

const refreshLogs = () => {
  logs.value = websocketService.getLogs();
  void scrollToBottom();
};

const clearLogs = () => {
  websocketService.clearLogs();
  logs.value = [];
};

const scrollToBottom = async (): Promise<void> => {
  await nextTick();
  if (scrollArea.value) {
    const scrollTarget = scrollArea.value.getScrollTarget();
    scrollArea.value.setScrollPosition('vertical', scrollTarget.scrollHeight, 0);
  }
};

const getLogClass = (log: string): string => {
  if (log.includes('🔵') || log.includes('🟢')) return 'log-websocket';
  if (log.includes('🤖')) return 'log-ai';
  if (log.includes('🔬')) return 'log-evaluation';
  if (log.includes('📤')) return 'log-send';
  if (log.includes('❌')) return 'log-error';
  if (log.includes('✅')) return 'log-success';
  return 'log-default';
};

// 自动刷新日志
watch(() => websocketService.getLogs().length, () => {
  refreshLogs();
});

// 初始化
refreshLogs();
</script>

<style scoped lang="scss">
.debug-panel {
  background: #1e1e1e;
  color: #ffffff;
}

.debug-header {
  background: #2d2d2d;
  border-bottom: 1px solid #444;
}

.debug-content {
  padding: 0;
}

.log-container {
  background: #1e1e1e;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.log-list {
  padding: 16px;
}

.log-entry {
  margin-bottom: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;

  &.log-websocket {
    background: rgba(33, 150, 243, 0.1);
    border-left: 3px solid #2196f3;
  }

  &.log-ai {
    background: rgba(76, 175, 80, 0.1);
    border-left: 3px solid #4caf50;
  }

  &.log-evaluation {
    background: rgba(255, 152, 0, 0.1);
    border-left: 3px solid #ff9800;
  }

  &.log-send {
    background: rgba(156, 39, 176, 0.1);
    border-left: 3px solid #9c27b0;
  }

  &.log-error {
    background: rgba(244, 67, 54, 0.1);
    border-left: 3px solid #f44336;
  }

  &.log-success {
    background: rgba(76, 175, 80, 0.1);
    border-left: 3px solid #4caf50;
  }

  &.log-default {
    background: rgba(158, 158, 158, 0.1);
    border-left: 3px solid #9e9e9e;
  }
}

.no-logs {
  text-align: center;
  color: #666;
  padding: 32px;
  font-style: italic;
}
</style>
