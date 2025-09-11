<template>
  <q-dialog
    v-model="showDialog"
    persistent
    maximized
    transition-show="slide-up"
    transition-hide="slide-down"
  >
    <q-card class="prompt-result-card">
      <!-- 头部 -->
      <q-card-section class="prompt-header bg-primary text-white">
        <div class="row items-center no-wrap">
          <div class="col">
            <div class="text-h5">
              <q-icon name="auto_awesome" class="q-mr-sm" />
              最终提示词已生成
            </div>
            <div class="text-subtitle2 opacity-80">
              角色扮演提示词 - {{ formatDate(timestamp) }}
            </div>
          </div>
          <div class="col-auto">
            <q-btn
              flat
              round
              dense
              icon="close"
              @click="$emit('close')"
              class="text-white"
            />
          </div>
        </div>
      </q-card-section>

      <!-- 内容区域 -->
      <q-card-section class="prompt-content">
        <div class="row q-gutter-md">
          <!-- 左侧：原始 Markdown -->
          <div class="col-12 col-md-6">
            <q-card flat bordered class="full-height">
              <q-card-section class="q-pb-none">
                <div class="text-h6 text-grey-8">
                  <q-icon name="code" class="q-mr-sm" />
                  Markdown 原文
                </div>
              </q-card-section>

              <q-card-section class="prompt-raw">
                <q-scroll-area style="height: 60vh;">
                  <pre class="markdown-text">{{ content }}</pre>
                </q-scroll-area>
              </q-card-section>

              <q-card-actions align="right">
                <q-btn
                  flat
                  icon="content_copy"
                  label="复制 Markdown"
                  color="primary"
                  @click="copyMarkdown"
                />
                <q-btn
                  flat
                  icon="download"
                  label="下载 .md"
                  color="secondary"
                  @click="downloadMarkdown"
                />
              </q-card-actions>
            </q-card>
          </div>

          <!-- 右侧：渲染预览 -->
          <div class="col-12 col-md-6">
            <q-card flat bordered class="full-height">
              <q-card-section class="q-pb-none">
                <div class="text-h6 text-grey-8">
                  <q-icon name="preview" class="q-mr-sm" />
                  预览效果
                </div>
              </q-card-section>

              <q-card-section class="prompt-preview">
                <q-scroll-area style="height: 60vh;">
                  <div class="markdown-content" v-html="renderedContent"></div>
                </q-scroll-area>
              </q-card-section>

              <q-card-actions align="right">
                <q-btn
                  flat
                  icon="content_copy"
                  label="复制文本"
                  color="primary"
                  @click="copyPlainText"
                />
                <q-btn
                  flat
                  icon="download"
                  label="下载 .txt"
                  color="secondary"
                  @click="downloadPlainText"
                />
              </q-card-actions>
            </q-card>
          </div>
        </div>
      </q-card-section>

      <!-- 底部操作区 -->
      <q-card-section class="prompt-actions bg-grey-2">
        <div class="row items-center justify-between">
          <div class="col-auto">
            <q-chip
              icon="psychology"
              color="positive"
              text-color="white"
              class="q-mr-sm"
            >
              提示词已完成
            </q-chip>

            <q-chip
              icon="schedule"
              color="info"
              text-color="white"
            >
              {{ formatTime(timestamp) }}
            </q-chip>
          </div>

          <div class="col-auto">
            <q-btn
              unelevated
              icon="refresh"
              label="开始新对话"
              color="primary"
              @click="$emit('new-chat')"
              class="q-mr-sm"
            />

            <q-btn
              flat
              icon="close"
              label="关闭"
              color="grey-7"
              @click="$emit('close')"
            />
          </div>
        </div>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { marked } from 'marked';
import { copyToClipboard, Notify } from 'quasar';

interface Props {
  show: boolean;
  content: string;
  timestamp: Date;
}

interface Emits {
  (e: 'close'): void;
  (e: 'new-chat'): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const showDialog = computed({
  get: () => props.show,
  set: (value: boolean) => {
    if (!value) {
      emit('close');
    }
  }
});

const renderedContent = computed(() => {
  try {
    return marked(props.content);
  } catch (error) {
    console.error('Markdown rendering error:', error);
    return '<p>渲染错误</p>';
  }
});

const plainTextContent = computed(() => {
  // 移除 Markdown 格式，保留纯文本
  return props.content
    .replace(/#{1,6}\s+/g, '') // 移除标题标记
    .replace(/\*\*(.*?)\*\*/g, '$1') // 移除粗体标记
    .replace(/\*(.*?)\*/g, '$1') // 移除斜体标记
    .replace(/`(.*?)`/g, '$1') // 移除代码标记
    .replace(/\[(.*?)\]\(.*?\)/g, '$1') // 移除链接，保留文本
    .replace(/^\s*[-*+]\s+/gm, '• ') // 转换列表项
    .replace(/^\s*\d+\.\s+/gm, '') // 移除数字列表标记
    .trim();
});

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
    minute: '2-digit',
    second: '2-digit'
  });
};

const copyMarkdown = async (): Promise<void> => {
  try {
    await copyToClipboard(props.content);
    Notify.create({
      type: 'positive',
      message: '已复制 Markdown 格式到剪贴板',
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

const copyPlainText = async (): Promise<void> => {
  try {
    await copyToClipboard(plainTextContent.value);
    Notify.create({
      type: 'positive',
      message: '已复制纯文本到剪贴板',
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

const downloadMarkdown = (): void => {
  downloadFile(props.content, 'roleplay-prompt.md', 'text/markdown');
  Notify.create({
    type: 'positive',
    message: 'Markdown 文件已下载',
    position: 'top'
  });
};

const downloadPlainText = (): void => {
  downloadFile(plainTextContent.value, 'roleplay-prompt.txt', 'text/plain');
  Notify.create({
    type: 'positive',
    message: '文本文件已下载',
    position: 'top'
  });
};

const downloadFile = (content: string, filename: string, mimeType: string): void => {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
};
</script>

<style scoped lang="scss">
.prompt-result-card {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.prompt-header {
  flex-shrink: 0;
}

.prompt-content {
  flex: 1;
  overflow: hidden;
}

.prompt-actions {
  flex-shrink: 0;
}

.prompt-raw {
  background-color: #f8f9fa;
  border-radius: 4px;
}

.markdown-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  background: transparent;
  color: #333;
}

.prompt-preview {
  background-color: #ffffff;
  border-radius: 4px;
}

.markdown-content {
  line-height: 1.8;
  color: #2c3e50;

  :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
    margin-top: 1.5em;
    margin-bottom: 0.75em;
    font-weight: 600;
    color: #2c3e50;

    &:first-child {
      margin-top: 0;
    }
  }

  :deep(h1) { font-size: 2em; border-bottom: 2px solid #eee; padding-bottom: 0.3em; }
  :deep(h2) { font-size: 1.7em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
  :deep(h3) { font-size: 1.4em; }
  :deep(h4) { font-size: 1.2em; }
  :deep(h5) { font-size: 1.1em; }
  :deep(h6) { font-size: 1em; }

  :deep(p) {
    margin-bottom: 1.2em;
    text-align: justify;
  }

  :deep(strong) {
    font-weight: 600;
    color: #2c3e50;
  }

  :deep(em) {
    font-style: italic;
    color: #34495e;
  }

  :deep(ul), :deep(ol) {
    margin-left: 2em;
    margin-bottom: 1.2em;

    li {
      margin-bottom: 0.5em;
    }
  }

  :deep(blockquote) {
    border-left: 4px solid #3498db;
    background-color: #f8f9fa;
    padding: 1em 1.5em;
    margin: 1.5em 0;
    font-style: italic;
    color: #5a6c7d;
    border-radius: 0 4px 4px 0;
  }

  :deep(code) {
    background-color: #f1f2f6;
    padding: 2px 6px;
    border-radius: 3px;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9em;
    color: #e74c3c;
  }

  :deep(pre) {
    background-color: #2c3e50;
    color: #ecf0f1;
    padding: 1.5em;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1.5em 0;

    code {
      background: transparent;
      color: inherit;
      padding: 0;
    }
  }

  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5em 0;

    th, td {
      border: 1px solid #ddd;
      padding: 12px;
      text-align: left;
    }

    th {
      background-color: #f8f9fa;
      font-weight: 600;
    }

    tr:nth-child(even) {
      background-color: #f8f9fa;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .row.q-gutter-md > div {
    width: 100% !important;
  }
}

// 暗色主题支持
.body--dark {
  .prompt-raw {
    background-color: #2d3748;
  }

  .markdown-text {
    color: #e2e8f0;
  }

  .prompt-preview {
    background-color: #2d3748;
  }

  .markdown-content {
    color: #e2e8f0;

    :deep(h1), :deep(h2), :deep(h3), :deep(h4), :deep(h5), :deep(h6) {
      color: #f7fafc;
    }

    :deep(blockquote) {
      background-color: #4a5568;
      color: #cbd5e0;
    }

    :deep(code) {
      background-color: #4a5568;
      color: #f56565;
    }

    :deep(pre) {
      background-color: #1a202c;
      color: #f7fafc;
    }
  }
}
</style>
