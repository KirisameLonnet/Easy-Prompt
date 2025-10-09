<template>
  <q-card class="enhanced-evaluation-card" flat bordered>
    <q-card-section class="panel-header" :class="headerClass">
      <div class="text-subtitle1" :class="headerTextClass">
        <q-icon :name="statusIcon" class="q-mr-sm" />
        评估状态
      </div>
      <div class="text-caption" :class="headerTextClass">
        {{ statusSummary }}
      </div>
    </q-card-section>

    <q-card-section class="panel-content q-pa-none">
      <q-scroll-area
        class="evaluation-scroll-area fit"
        :thumb-style="{ width: '6px', borderRadius: '3px', opacity: '0.5' }"
        :bar-style="{ width: '6px' }"
      >
        <div class="scroll-content-wrapper q-pa-md">
          <!-- 当前状态显示 -->
          <div v-if="showEvaluationCard" class="evaluation-progress">
            <div class="progress-header">
              <q-spinner-dots color="orange" size="md" class="q-mr-sm" />
              <span class="text-body2 text-orange-8">正在评估中...</span>
            </div>
            <div class="progress-message q-mt-sm">
              <q-icon name="info" size="sm" color="orange" class="q-mr-xs" />
              <span class="text-caption text-grey-7">{{ evaluationStatus }}</span>
            </div>
          </div>

          <!-- 已确认特性和关键词显示 -->
          <div v-if="hasExtractedContent" class="traits-section">
            <div class="section-header">
              <q-icon name="verified" color="positive" size="md" class="q-mr-sm" />
              <span class="text-subtitle2 text-positive">已确认特性</span>
              <q-chip
                size="sm"
                color="positive"
                text-color="white"
                :label="extractedTraits.length"
                class="q-ml-sm"
              />
            </div>

            <!-- 特性标签列表 -->
            <div class="traits-grid q-mt-md">
              <q-chip
                v-for="(trait, index) in extractedTraits"
                :key="`trait-${index}`"
                size="sm"
                color="orange-1"
                text-color="orange-8"
                icon="check_circle"
                class="trait-chip"
                clickable
                @click="showTraitDetail(trait)"
              >
                {{ trait }}
              </q-chip>
            </div>

            <!-- 关键词显示 -->
            <div v-if="extractedKeywords && extractedKeywords.length > 0" class="keywords-section q-mt-md">
              <div class="section-header">
                <q-icon name="label" color="primary" size="md" class="q-mr-sm" />
                <span class="text-subtitle2 text-primary">相关关键词</span>
                <q-chip
                  size="sm"
                  color="primary"
                  text-color="white"
                  :label="extractedKeywords?.length || 0"
                  class="q-ml-sm"
                />
              </div>

              <div class="keywords-grid q-mt-sm">
                <q-chip
                  v-for="(keyword, index) in (extractedKeywords || [])"
                  :key="`keyword-${index}`"
                  size="xs"
                  color="blue-1"
                  text-color="blue-8"
                  icon="tag"
                  class="keyword-chip"
                >
                  {{ keyword }}
                </q-chip>
              </div>
            </div>

            <!-- 评估分数显示 -->
            <div v-if="evaluationScore != null" class="score-section q-mt-md">
              <div class="section-header">
                <q-icon name="analytics" color="info" size="md" class="q-mr-sm" />
                <span class="text-subtitle2 text-info">完整度评分</span>
              </div>

              <div class="score-display q-mt-sm">
                <q-circular-progress
                  :value="(evaluationScore || 0) * 10"
                  size="60px"
                  :thickness="0.15"
                  color="info"
                  track-color="grey-3"
                  class="q-mr-md"
                >
                  <div class="text-h6 text-info">{{ evaluationScore || 0 }}/10</div>
                </q-circular-progress>

                <div class="score-text">
                  <div class="text-body2">{{ getScoreDescription(evaluationScore || 0) }}</div>
                  <div class="text-caption text-grey-6 q-mt-xs">
                    {{ getScoreAdvice(evaluationScore || 0) }}
                  </div>
                </div>
              </div>

              <!-- 优秀评分提示 - 建议生成提示词 -->
              <q-banner
                v-if="evaluationScore != null && evaluationScore >= 9"
                class="q-mt-md generate-prompt-banner"
                rounded
                dense
              >
                <template v-slot:avatar>
                  <q-icon name="rocket_launch" color="positive" size="md" />
                </template>
                <div class="text-subtitle2 text-positive q-mb-xs">
                  🎉 角色已完善！
                </div>
                <div class="text-caption text-grey-7">
                  您的角色设定已经非常完整，建议立即生成提示词
                </div>
                <template v-slot:action>
                  <q-btn
                    unelevated
                    color="positive"
                    label="生成提示词"
                    icon="auto_awesome"
                    size="sm"
                    @click="$emit('generate-prompt')"
                  />
                </template>
              </q-banner>
            </div>

            <!-- 完整度指标 -->
            <div class="completeness-indicators q-mt-md">
              <div class="section-header">
                <q-icon name="checklist" color="purple" size="md" class="q-mr-sm" />
                <span class="text-subtitle2 text-purple">完整度指标</span>
              </div>

              <div class="indicators-list q-mt-sm">
                <div
                  v-for="indicator in completenessIndicators"
                  :key="indicator.key"
                  class="indicator-item"
                >
                  <q-icon
                    :name="indicator.completed ? 'check_circle' : 'radio_button_unchecked'"
                    :color="indicator.completed ? 'positive' : 'grey-4'"
                    size="sm"
                    class="q-mr-sm"
                  />
                  <span
                    class="text-body2"
                    :class="indicator.completed ? 'text-positive' : 'text-grey-6'"
                  >
                    {{ indicator.label }}
                  </span>
                  <q-chip
                    v-if="indicator.count > 0"
                    size="xs"
                    :color="indicator.completed ? 'positive' : 'grey-3'"
                    :text-color="indicator.completed ? 'white' : 'grey-6'"
                    :label="indicator.count"
                    class="q-ml-sm"
                  />
                </div>
              </div>
            </div>

            <!-- 操作按钮区域 - 确保有足够的底部空间 -->
            <div v-if="hasExtractedContent" class="action-buttons q-mt-lg">
              <div class="row justify-center q-gutter-sm q-mb-sm">
                <q-btn
                  unelevated
                  icon="auto_awesome"
                  label="生成提示词"
                  color="positive"
                  size="md"
                  @click="$emit('generate-prompt')"
                  class="full-width"
                  :disable="evaluationScore != null && evaluationScore < 3"
                >
                  <q-tooltip v-if="evaluationScore != null && evaluationScore < 3">
                    评分过低，建议继续补充角色特征后再生成
                  </q-tooltip>
                </q-btn>
              </div>
              <div class="row justify-center q-gutter-sm">
                <q-btn
                  flat
                  icon="refresh"
                  label="重新评估"
                  color="orange"
                  size="sm"
                  @click="$emit('re-evaluate')"
                />
                <q-btn
                  flat
                  icon="visibility"
                  label="详细报告"
                  color="primary"
                  size="sm"
                  @click="showDetailDialog = true"
                />
              </div>
            </div>

            <!-- 额外的底部占位空间，确保可以完整滚动 -->
            <div class="bottom-spacer"></div>
          </div>

          <!-- 空状态显示 -->
          <div v-if="!showEvaluationCard && !hasExtractedContent">
            <div class="empty-state">
              <q-icon name="psychology" size="3rem" color="grey-4" class="q-mb-md" />
              <div class="text-body2 text-grey-5 text-center">等待评估...</div>
              <div class="text-caption text-grey-4 text-center q-mt-xs">
                开始描述角色特征后，这里会显示评估结果
              </div>
            </div>
            <!-- 空状态也需要底部占位 -->
            <div class="bottom-spacer"></div>
          </div>
        </div>
      </q-scroll-area>
    </q-card-section>

    <!-- 特性详情对话框 -->
    <q-dialog v-model="showDetailDialog" maximized>
      <q-card>
        <q-card-section class="row items-center q-pb-none">
          <div class="text-h6">详细评估报告</div>
          <q-space />
          <q-btn icon="close" flat round dense v-close-popup />
        </q-card-section>

        <q-card-section>
          <div class="evaluation-detail">
            <!-- 详细内容在这里展示 -->
            <pre class="detail-text">{{ formatDetailReport() }}</pre>
          </div>
        </q-card-section>
      </q-card>
    </q-dialog>
  </q-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  evaluationStatus: string;
  showEvaluationCard: boolean;
  extractedTraits: string[];
  evaluationScore?: number | null;
  extractedKeywords?: string[];
  completenessData?: {
    core_identity: number;
    personality_traits: number;
    behavioral_patterns: number;
    interaction_patterns: number;
  };
}

interface Emits {
  (e: 're-evaluate'): void;
  (e: 'trait-selected', trait: string): void;
  (e: 'generate-prompt'): void;
}

const props = withDefaults(defineProps<Props>(), {
  extractedKeywords: () => [],
  evaluationScore: null,
  completenessData: () => ({
    core_identity: 0,
    personality_traits: 0,
    behavioral_patterns: 0,
    interaction_patterns: 0
  })
});

const emit = defineEmits<Emits>();

const showDetailDialog = ref(false);

// 计算属性
const hasExtractedContent = computed(() =>
  props.extractedTraits.length > 0 || (props.extractedKeywords && props.extractedKeywords.length > 0)
);

const statusIcon = computed(() => {
  if (props.showEvaluationCard) return 'psychology';
  if (hasExtractedContent.value) return 'verified';
  return 'psychology';
});

const headerClass = computed(() => {
  if (props.showEvaluationCard) return 'bg-orange-1';
  if (hasExtractedContent.value) return 'bg-positive-1';
  return 'bg-grey-1';
});

const headerTextClass = computed(() => {
  if (props.showEvaluationCard) return 'text-orange-8';
  if (hasExtractedContent.value) return 'text-positive-8';
  return 'text-grey-6';
});

const statusSummary = computed(() => {
  if (props.showEvaluationCard) return '分析中...';
  if (hasExtractedContent.value) {
    return `已识别 ${props.extractedTraits.length} 个特性`;
  }
  return '等待输入';
});

const completenessIndicators = computed(() => {
  const data = props.completenessData || {};
  return [
    {
      key: 'core_identity',
      label: '核心身份',
      count: data.core_identity || 0,
      completed: (data.core_identity || 0) > 0
    },
    {
      key: 'personality_traits',
      label: '性格特质',
      count: data.personality_traits || 0,
      completed: (data.personality_traits || 0) > 0
    },
    {
      key: 'behavioral_patterns',
      label: '行为模式',
      count: data.behavioral_patterns || 0,
      completed: (data.behavioral_patterns || 0) > 0
    },
    {
      key: 'interaction_patterns',
      label: '互动方式',
      count: data.interaction_patterns || 0,
      completed: (data.interaction_patterns || 0) > 0
    }
  ];
});

// 方法
const showTraitDetail = (trait: string): void => {
  emit('trait-selected', trait);
};

const getScoreDescription = (score: number): string => {
  if (score >= 9) return '优秀';
  if (score >= 7) return '良好';
  if (score >= 5) return '一般';
  if (score >= 3) return '需要改进';
  return '刚开始';
};

const getScoreAdvice = (score: number): string => {
  if (score >= 9) return '角色已经非常完整，可以生成提示词';
  if (score >= 7) return '角色基本完整，可以考虑添加更多细节';
  if (score >= 5) return '角色框架已建立，需要补充具体特征';
  if (score >= 3) return '角色轮廓初现，建议继续完善';
  return '刚开始创建，继续描述角色特征';
};

const formatDetailReport = (): string => {
  const report = [];
  report.push('=== 详细评估报告 ===\n');

  report.push('已确认特性:');
  props.extractedTraits.forEach((trait, index) => {
    report.push(`${index + 1}. ${trait}`);
  });

  if (props.extractedKeywords && props.extractedKeywords.length > 0) {
    report.push('\n相关关键词:');
    report.push(props.extractedKeywords.join(', '));
  }

  if (props.evaluationScore != null) {
    report.push(`\n完整度评分: ${props.evaluationScore}/10`);
  }

  report.push('\n完整度指标:');
  completenessIndicators.value.forEach(indicator => {
    const status = indicator.completed ? '✓' : '○';
    report.push(`${status} ${indicator.label}: ${indicator.count} 项`);
  });

  return report.join('\n');
};
</script>

<style scoped lang="scss">
.enhanced-evaluation-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  flex-shrink: 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.panel-content {
  flex: 1;
  overflow: hidden;
  min-height: 0; // 关键：允许 flex 子元素正确缩小
}

.scroll-content-wrapper {
  // 移除默认的底部padding，改用bottom-spacer
  padding-bottom: 0 !important;
}

.evaluation-scroll-area {
  width: 100%;

  // 优化滚动条样式
  :deep(.q-scrollarea__thumb) {
    opacity: 0.5;
    transition: opacity 0.3s;
    background: #ff9800;

    &:hover {
      opacity: 0.8;
    }
  }

  // 修复SASS语法错误：直接使用完整选择器
  :deep(.q-scrollarea__bar--v) {
    width: 6px;
    opacity: 1;
  }
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.traits-grid, .keywords-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.trait-chip {
  transition: all 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
}

.keyword-chip {
  font-size: 0.7rem;
}

.score-display {
  display: flex;
  align-items: center;
}

.score-text {
  flex: 1;
}

.indicator-item {
  display: flex;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);

  &:last-child {
    border-bottom: none;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  text-align: center;
}

.action-buttons {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  padding-top: 16px;
  margin-top: 16px;
}

// 底部占位空间，确保可以完整滚动到按钮下方
.bottom-spacer {
  height: 32px;
  flex-shrink: 0;
}

.progress-header {
  display: flex;
  align-items: center;
}

.progress-message {
  display: flex;
  align-items: center;
  background: rgba(255, 152, 0, 0.05);
  padding: 8px;
  border-radius: 4px;
  border-left: 3px solid #ff9800;
}

.generate-prompt-banner {
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border: 2px solid #4caf50;
  box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
  animation: pulse-border 2s ease-in-out infinite;

  :deep(.q-banner__avatar) {
    font-size: 2rem;
  }

  :deep(.q-btn) {
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(76, 175, 80, 0.3);

    &:hover {
      box-shadow: 0 4px 12px rgba(76, 175, 80, 0.4);
    }
  }
}

@keyframes pulse-border {
  0%, 100% {
    border-color: #4caf50;
  }
  50% {
    border-color: #66bb6a;
  }
}

.evaluation-detail {
  background: #f5f5f5;
  border-radius: 4px;
  padding: 16px;
}

.detail-text {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  white-space: pre-wrap;
  margin: 0;
}

// 响应式设计
@media (max-width: 768px) {
  .panel-header {
    padding: 10px 12px !important;

    .text-subtitle1 {
      font-size: 0.9rem;
    }

    .text-caption {
      font-size: 0.7rem;
    }
  }

  .scroll-content-wrapper {
    padding: 12px !important;
  }

  .section-header {
    .text-subtitle2 {
      font-size: 0.85rem;
    }

    .q-icon {
      font-size: 1.2rem;
    }
  }

  .score-display {
    flex-direction: column;
    text-align: center;

    .q-circular-progress {
      margin-bottom: 8px;
      margin-right: 0;
    }
  }

  .traits-grid, .keywords-grid {
    gap: 6px;
  }

  .trait-chip, .keyword-chip {
    font-size: 0.75rem;
  }

  .action-buttons {
    margin-top: 12px;
    padding-top: 12px;

    .q-btn {
      font-size: 0.75rem;
      padding: 4px 8px;
    }
  }

  .generate-prompt-banner {
    :deep(.q-banner__content) {
      font-size: 0.85rem;
    }

    :deep(.q-btn) {
      font-size: 0.75rem;
      padding: 6px 12px;
    }
  }
}

@media (max-width: 480px) {
  .panel-header {
    padding: 8px 10px !important;

    .text-subtitle1 {
      font-size: 0.85rem;
    }

    .text-caption {
      font-size: 0.65rem;
    }

    .q-icon {
      font-size: 1rem;
    }
  }

  .scroll-content-wrapper {
    padding: 10px !important;
  }

  .section-header {
    margin-bottom: 6px;

    .text-subtitle2 {
      font-size: 0.8rem;
    }

    .q-icon {
      font-size: 1rem;
      margin-right: 4px !important;
    }

    .q-chip {
      font-size: 0.65rem;
    }
  }

  .progress-header {
    .text-body2 {
      font-size: 0.8rem;
    }
  }

  .progress-message {
    padding: 6px;

    .text-caption {
      font-size: 0.7rem;
    }
  }

  .score-display {
    .q-circular-progress {
      font-size: 50px !important;
    }

    .text-h6 {
      font-size: 0.9rem;
    }

    .text-body2 {
      font-size: 0.75rem;
    }

    .text-caption {
      font-size: 0.65rem;
    }
  }

  .indicator-item {
    padding: 3px 0;

    .text-body2 {
      font-size: 0.75rem;
    }
  }

  .empty-state {
    height: 150px;

    .q-icon {
      font-size: 2rem !important;
    }

    .text-body2 {
      font-size: 0.8rem;
    }

    .text-caption {
      font-size: 0.7rem;
    }
  }

  .generate-prompt-banner {
    :deep(.q-banner__avatar) {
      font-size: 1.5rem !important;
    }

    :deep(.q-banner__content) {
      font-size: 0.8rem;
    }

    .text-subtitle2 {
      font-size: 0.85rem;
    }

    .text-caption {
      font-size: 0.7rem;
    }

    :deep(.q-btn) {
      font-size: 0.7rem;
      padding: 5px 10px;
    }
  }
}

// 暗色主题支持
.body--dark {
  .evaluation-detail {
    background: #2d2d2d;
    color: #e0e0e0;
  }

  .detail-text {
    color: #e0e0e0;
  }

  .progress-message {
    background: rgba(255, 152, 0, 0.1);
  }

  .generate-prompt-banner {
    background: linear-gradient(135deg, #1b5e20 0%, #2e7d32 100%);
    border-color: #66bb6a;
  }
}
</style>
