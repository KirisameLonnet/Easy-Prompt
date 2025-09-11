<template>
  <q-card
    v-if="show"
    class="evaluation-card"
    flat
    bordered
  >
    <q-card-section class="q-pa-md">
      <div class="evaluation-content">
        <div class="evaluation-icon">
          <q-icon name="psychology" color="orange" size="md" />
          <q-spinner-dots color="orange" size="sm" class="q-ml-sm" />
        </div>

        <div class="evaluation-text">
          <div class="text-subtitle2 text-orange-8">评估进行中</div>
          <div class="text-body2 text-grey-7">{{ message }}</div>
        </div>

        <q-btn
          flat
          round
          dense
          icon="close"
          color="grey-6"
          size="sm"
          @click="$emit('close')"
          class="evaluation-close"
        />
      </div>
    </q-card-section>

    <!-- 进度条 -->
    <q-linear-progress
      :value="progress"
      color="orange"
      size="2px"
      class="evaluation-progress"
    />
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue';

interface Props {
  show: boolean;
  message: string;
  autoHideDelay?: number; // 自动隐藏延迟（毫秒）
}

interface Emits {
  (e: 'close'): void;
}

const props = withDefaults(defineProps<Props>(), {
  autoHideDelay: 3000
});

const emit = defineEmits<Emits>();

const progress = ref(0);
let progressTimer: NodeJS.Timeout | null = null;
let autoHideTimer: NodeJS.Timeout | null = null;

const isVisible = computed(() => props.show);

// 监听显示状态变化
watch(isVisible, (newVal) => {
  if (newVal) {
    startProgress();
    startAutoHide();
  } else {
    clearTimers();
  }
});

const startProgress = (): void => {
  progress.value = 0;
  const duration = props.autoHideDelay;
  const steps = 60; // 60步完成进度
  const stepTime = duration / steps;

  progressTimer = setInterval(() => {
    progress.value += 1 / steps;
    if (progress.value >= 1) {
      clearInterval(progressTimer!);
      progressTimer = null;
    }
  }, stepTime);
};

const startAutoHide = (): void => {
  autoHideTimer = setTimeout(() => {
    emit('close');
  }, props.autoHideDelay);
};

const clearTimers = (): void => {
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  if (autoHideTimer) {
    clearTimeout(autoHideTimer);
    autoHideTimer = null;
  }
  progress.value = 0;
};

onUnmounted(() => {
  clearTimers();
});
</script>

<style scoped lang="scss">
.evaluation-card {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 320px;
  z-index: 1000;
  background-color: rgba(255, 248, 225, 0.95);
  border: 1px solid #ffb74d;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(255, 152, 0, 0.2);
  backdrop-filter: blur(10px);
  animation: slideInRight 0.3s ease-out;
}

.evaluation-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.evaluation-icon {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.evaluation-text {
  flex: 1;
  min-width: 0;
}

.evaluation-close {
  flex-shrink: 0;
  align-self: flex-start;
}

.evaluation-progress {
  margin: 0;
  border-radius: 0 0 8px 8px;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

// 响应式设计
@media (max-width: 600px) {
  .evaluation-card {
    position: fixed;
    top: 10px;
    left: 10px;
    right: 10px;
    width: auto;
  }
}

// 暗色主题支持
.body--dark .evaluation-card {
  background-color: rgba(66, 66, 66, 0.95);
  border-color: #ffb74d;
}
</style>
