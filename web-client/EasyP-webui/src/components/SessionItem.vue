<template>
  <div
    class="session-item"
    :class="{ 'active': isActive }"
    @click="$emit('click')"
  >
    <div class="session-content">
      <div class="session-icon">
        <q-icon name="chat" size="18px" />
      </div>

      <div class="session-info">
        <div class="session-name">{{ session.name }}</div>
        <div v-if="session.lastMessage" class="session-preview">
          {{ truncateMessage(session.lastMessage) }}
        </div>
      </div>
    </div>

    <div class="session-actions" v-show="showActions || isActive">
      <q-btn
        flat
        round
        dense
        size="sm"
        icon="edit"
        class="action-btn"
        @click.stop="$emit('rename', session.id, session.name)"
      >
        <q-tooltip>重命名</q-tooltip>
      </q-btn>

      <q-btn
        flat
        round
        dense
        size="sm"
        icon="delete"
        class="action-btn delete-btn"
        @click.stop="$emit('delete', session.id)"
      >
        <q-tooltip>删除</q-tooltip>
      </q-btn>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { Session } from 'src/types/websocket';

interface Props {
  session: Session;
  isActive?: boolean;
}

interface Emits {
  (e: 'click'): void;
  (e: 'rename', sessionId: string, currentName: string): void;
  (e: 'delete', sessionId: string): void;
}

withDefaults(defineProps<Props>(), {
  isActive: false
});

defineEmits<Emits>();

const showActions = ref(false);

const truncateMessage = (message: string, maxLength: number = 50): string => {
  if (message.length <= maxLength) return message;
  return message.substring(0, maxLength) + '...';
};
</script>

<style scoped lang="scss">
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  margin-bottom: 4px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  transform: translateX(0);

  &:hover {
    background-color: rgba(0, 0, 0, 0.05);
    transform: translateX(2px);

    .session-actions {
      display: flex !important;
      animation: slideIn 0.2s ease;
    }
  }

  &.active {
    background-color: #ececf1;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

    .session-name {
      color: #10a37f;
      font-weight: 500;
    }

    .session-icon {
      color: #10a37f;
    }
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.session-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.session-icon {
  flex-shrink: 0;
  color: #6e6e80;
  display: flex;
  align-items: center;
  transition: color 0.2s ease;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-name {
  font-size: 14px;
  color: #202123;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: all 0.2s ease;
}

.session-preview {
  font-size: 12px;
  color: #6e6e80;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}

.session-actions {
  display: none;
  gap: 4px;
  flex-shrink: 0;
  align-items: center;

  .action-btn {
    width: 28px;
    height: 28px;
    color: #6e6e80;

    &:hover {
      background-color: rgba(0, 0, 0, 0.08);
    }

    &.delete-btn:hover {
      color: #ef4444;
    }
  }
}

// 暗色主题支持
.body--dark {
  .session-item {
    &:hover {
      background-color: rgba(255, 255, 255, 0.05);
    }

    &.active {
      background-color: #2a2b32;

      .session-name {
        color: #10a37f;
      }

      .session-icon {
        color: #10a37f;
      }
    }
  }

  .session-name {
    color: #ececf1;
  }

  .session-icon {
    color: #8e8ea0;
  }

  .session-preview {
    color: #8e8ea0;
  }

  .action-btn {
    color: #8e8ea0;

    &:hover {
      background-color: rgba(255, 255, 255, 0.08);
    }

    &.delete-btn:hover {
      color: #ef4444;
    }
  }
}
</style>

