<template>
  <div class="chat-message" :class="messageClass">
    <div class="message-meta">
      <q-icon :name="messageIcon" :color="iconColor" size="sm" class="q-mr-xs" />
      <span class="message-time">{{ formatTime(message.timestamp) }}</span>
    </div>

    <div class="message-content">
      <div v-if="message.type === 'final_prompt'" class="final-prompt-container">
        <q-card class="final-prompt-card">
          <q-card-section>
            <div class="text-h6 q-mb-md">
              <q-icon name="auto_awesome" color="primary" />
              最终提示词
            </div>
            <div class="markdown-content" v-html="renderedContent"></div>
          </q-card-section>
          <q-card-actions align="right" v-if="message.isComplete">
            <q-btn
              flat
              icon="content_copy"
              label="复制"
              color="primary"
              @click="copyToClipboard"
            />
            <q-btn
              flat
              icon="download"
              label="下载"
              color="secondary"
              @click="downloadPrompt"
            />
          </q-card-actions>
        </q-card>
      </div>

      <div v-else class="message-text">
        <span v-html="renderedContent"></span>
        <q-spinner-dots
          v-if="!message.isComplete && ['ai', 'final_prompt'].includes(message.type)"
          color="primary"
          size="sm"
          class="q-ml-sm"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import { copyToClipboard as copyText, Notify } from 'quasar';
import type { ChatMessage } from 'src/types/websocket';

interface Props {
  message: ChatMessage;
}

const props = defineProps<Props>();

const messageClass = computed(() => {
  return {
    'chat-message--system': props.message.type === 'system',
    'chat-message--ai': props.message.type === 'ai',
    'chat-message--user': props.message.type === 'user',
    'chat-message--final-prompt': props.message.type === 'final_prompt',
    'chat-message--error': props.message.type === 'error',
    'chat-message--incomplete': !props.message.isComplete
  };
});

const messageIcon = computed(() => {
  switch (props.message.type) {
    case 'system': return 'info';
    case 'ai': return 'smart_toy';
    case 'user': return 'person';
    case 'final_prompt': return 'auto_awesome';
    case 'error': return 'error';
    default: return 'message';
  }
});

const iconColor = computed(() => {
  switch (props.message.type) {
    case 'system': return 'info';
    case 'ai': return 'primary';
    case 'user': return 'secondary';
    case 'final_prompt': return 'positive';
    case 'error': return 'negative';
    default: return 'grey';
  }
});

const renderedContent = computed(() => {
  if (props.message.type === 'final_prompt') {
    // 渲染 Markdown
    return marked(props.message.content);
  } else {
    // 简单的文本渲染，保留换行
    return props.message.content.replace(/\n/g, '<br>');
  }
});

const formatTime = (timestamp: Date): string => {
  return timestamp.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const copyToClipboard = async (): Promise<void> => {
  try {
    await copyText(props.message.content);
    Notify.create({
      type: 'positive',
      message: '已复制到剪贴板',
      position: 'top'
    });
  } catch {
    Notify.create({
      type: 'negative',
      message: '复制失败',
      position: 'top'
    });
  }
};

const downloadPrompt = (): void => {
  const blob = new Blob([props.message.content], { type: 'text/markdown' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `roleplay-prompt-${Date.now()}.md`;
  a.click();
  URL.revokeObjectURL(url);

  Notify.create({
    type: 'positive',
    message: '提示词已下载',
    position: 'top'
  });
};
</script>

<style scoped lang="scss">
.chat-message {
  margin-bottom: 16px;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;

  &--system {
    background-color: rgba(33, 150, 243, 0.1);
    border-left: 4px solid #2196f3;
  }

  &--ai {
    background-color: rgba(103, 58, 183, 0.1);
    border-left: 4px solid #673ab7;
  }

  &--user {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4caf50;
    margin-left: 20%;
  }

  &--final-prompt {
    background-color: rgba(139, 195, 74, 0.1);
    border-left: 4px solid #8bc34a;
  }

  &--error {
    background-color: rgba(244, 67, 54, 0.1);
    border-left: 4px solid #f44336;
  }

  &--incomplete {
    opacity: 0.9;
  }
}

.message-meta {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.message-time {
  font-family: monospace;
}

.message-content {
  line-height: 1.6;
}

.message-text {
  word-wrap: break-word;
  white-space: pre-wrap;
}

.final-prompt-container {
  .final-prompt-card {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(139, 195, 74, 0.3);
  }
}

.markdown-content {
  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 1em;
    margin-bottom: 0.5em;
    color: #2c3e50;
  }

  :deep(p) {
    margin-bottom: 1em;
  }

  :deep(strong) {
    font-weight: 600;
    color: #2c3e50;
  }

  :deep(ul), :deep(ol) {
    margin-left: 1.5em;
    margin-bottom: 1em;
  }

  :deep(blockquote) {
    border-left: 4px solid #ddd;
    padding-left: 1em;
    margin: 1em 0;
    font-style: italic;
    color: #666;
  }

  :deep(code) {
    background-color: #f5f5f5;
    padding: 2px 4px;
    border-radius: 3px;
    font-family: monospace;
  }

  :deep(pre) {
    background-color: #f5f5f5;
    padding: 1em;
    border-radius: 4px;
    overflow-x: auto;
    margin: 1em 0;
  }
}
</style>
