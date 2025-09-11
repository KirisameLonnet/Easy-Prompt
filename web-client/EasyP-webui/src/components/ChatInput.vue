<template>
  <div class="chat-input-container">
    <!-- 确认对话框 -->
    <div
      v-if="showConfirmation"
      class="confirmation-section q-mb-md"
    >
      <q-card class="confirmation-card" flat bordered>
        <q-card-section>
          <div class="text-h6 text-primary q-mb-sm">
            <q-icon name="help" class="q-mr-sm" />
            需要确认
          </div>
          <p class="text-body1 q-mb-md">{{ confirmationReason }}</p>

          <div class="confirmation-actions">
            <q-btn
              flat
              label="拒绝"
              color="negative"
              @click="handleConfirmation(false)"
              :disable="loading"
              class="q-mr-sm"
            />
            <q-btn
              unelevated
              label="确认生成"
              color="positive"
              @click="handleConfirmation(true)"
              :loading="loading"
            />
          </div>
        </q-card-section>
      </q-card>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <q-input
        v-model="inputText"
        type="textarea"
        placeholder="请描述你想要的角色..."
        autogrow
        :rows="2"
        :max-height="120"
        outlined
        :disable="!canInput"
        @keydown.ctrl.enter="sendMessage"
        @keydown.meta.enter="sendMessage"
        class="message-input"
      >
        <template v-slot:append>
          <q-btn
            round
            dense
            flat
            icon="send"
            color="primary"
            @click="sendMessage"
            :disable="!canSend"
            :loading="loading"
          />
        </template>
      </q-input>
    </div>

    <div class="input-controls q-mt-sm">
      <div class="connection-status">
        <template v-if="connectionStatus === 'connected'">
          <q-icon name="circle" color="positive" size="xs" class="q-mr-xs" />
          <span class="text-caption text-positive">已连接</span>
        </template>
        <template v-else-if="connectionStatus === 'connecting'">
          <q-spinner size="xs" class="q-mr-xs" />
          <span class="text-caption text-grey-6">连接中...</span>
        </template>
        <template v-else-if="connectionStatus === 'disconnected'">
          <q-icon name="circle" color="grey" size="xs" class="q-mr-xs" />
          <span class="text-caption text-grey-6">未连接</span>
        </template>
        <template v-else>
          <q-icon name="circle" color="negative" size="xs" class="q-mr-xs" />
          <span class="text-caption text-negative">连接错误</span>
        </template>
      </div>

      <div class="input-actions">
        <q-btn
          v-if="connectionStatus === 'disconnected'"
          flat
          dense
          label="重新连接"
          color="primary"
          size="sm"
          @click="$emit('reconnect')"
          class="q-mr-sm"
        />

        <q-btn
          flat
          dense
          label="清空对话"
          color="grey"
          size="sm"
          @click="confirmClear"
          :disable="messages.length === 0"
        />
      </div>
    </div>
  </div>
</template><script setup lang="ts">
import { ref, computed, nextTick } from 'vue';
import { Dialog, Notify } from 'quasar';
import type { ChatMessage, ConnectionStatus, AppState } from 'src/types/websocket';

interface Props {
  connectionStatus: ConnectionStatus;
  appState: AppState;
  messages: ChatMessage[];
  confirmationReason?: string;
  loading?: boolean;
}

interface Emits {
  (e: 'sendMessage', message: string): void;
  (e: 'sendConfirmation', confirm: boolean): void;
  (e: 'reconnect'): void;
  (e: 'clear'): void;
}

const props = withDefaults(defineProps<Props>(), {
  confirmationReason: '',
  loading: false
});

const emit = defineEmits<Emits>();

const inputText = ref('');

const showConfirmation = computed(() => {
  return props.appState === 'awaiting_confirmation' && props.confirmationReason;
});

const canInput = computed(() => {
  return props.connectionStatus === 'connected' &&
         props.appState === 'chatting' &&
         !props.loading;
});

const canSend = computed(() => {
  return canInput.value && inputText.value.trim().length > 0;
});

const sendMessage = (): void => {
  if (!canSend.value) return;

  const message = inputText.value.trim();
  if (message) {
    emit('sendMessage', message);
    inputText.value = '';
  }
};

const handleConfirmation = (confirm: boolean): void => {
  emit('sendConfirmation', confirm);
};

const confirmClear = (): void => {
  Dialog.create({
    title: '确认清空',
    message: '确定要清空所有对话记录吗？此操作不可恢复。',
    cancel: true,
    persistent: true
  }).onOk(() => {
    emit('clear');
    Notify.create({
      type: 'info',
      message: '对话记录已清空',
      position: 'top'
    });
  });
};

// 提供焦点方法给父组件
const focusInput = async (): Promise<void> => {
  await nextTick();
  const input = document.querySelector('.message-input input') as HTMLInputElement;
  input?.focus();
};

defineExpose({
  focusInput
});
</script>

<style scoped lang="scss">
.chat-input-container {
  background-color: transparent;
}

.confirmation-section {
  .confirmation-card {
    border: 2px solid #2196f3;
    background-color: rgba(33, 150, 243, 0.05);
    border-radius: 8px;
  }

  .confirmation-actions {
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }
}

.input-area {
  .message-input {
    :deep(.q-field__control) {
      border-radius: 8px;
      background-color: white;
    }

    :deep(textarea) {
      resize: none;
    }
  }
}

.input-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.connection-status {
  display: flex;
  align-items: center;
}

.input-actions {
  display: flex;
  align-items: center;
}

@media (max-width: 600px) {
  .input-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .input-actions {
    align-self: flex-end;
  }
}
</style>
