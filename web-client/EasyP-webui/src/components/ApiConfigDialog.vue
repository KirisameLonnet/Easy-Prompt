<template>
  <q-dialog v-model="showDialog" persistent max-width="600px">
    <q-card class="api-config-card">
      <q-card-section class="bg-primary text-white">
        <div class="text-h6">
          <q-icon name="settings" class="q-mr-sm" />
          API 配置
        </div>
        <div class="text-caption">
          配置后端API服务提供商 - 所有字段都是必填的
        </div>
      </q-card-section>

      <q-card-section>
        <!-- API类型选择 -->
        <div class="q-mb-md">
          <q-option-group
            v-model="localConfig.api_type"
            :options="apiTypeOptions"
            color="primary"
            inline
            @update:model-value="onApiTypeChange"
          />
        </div>

        <!-- Gemini 配置 -->
        <div v-if="localConfig.api_type === 'gemini'" class="gemini-config">
          <div class="row q-gutter-md">
            <div class="col-12">
              <q-input
                v-model="localConfig.api_key"
                label="Google API Key *"
                type="password"
                outlined
                dense
                :rules="[val => !!val || 'Google API Key是必填项']"
              >
                <template v-slot:prepend>
                  <q-icon name="key" />
                </template>
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="localConfig.model"
                label="对话模型 *"
                outlined
                dense
                placeholder="如: gemini-2.5-flash, gemini-2.5-pro"
                :rules="[val => !!val || '模型名称是必填项']"
              >
                <template v-slot:prepend>
                  <q-icon name="psychology" />
                </template>
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="localConfig.evaluator_model"
                label="评估模型"
                outlined
                dense
                placeholder="如: gemini-2.5-flash (留空则使用对话模型)"
              >
                <template v-slot:prepend>
                  <q-icon name="assessment" />
                </template>
              </q-input>
            </div>

            <div class="col-6">
              <q-input
                v-model.number="localConfig.temperature"
                label="Temperature"
                type="number"
                outlined
                dense
                step="0.1"
                min="0"
                max="2"
                :rules="[val => val >= 0 && val <= 2 || 'Temperature应在0-2之间']"
              >
                <template v-slot:prepend>
                  <q-icon name="thermostat" />
                </template>
              </q-input>
            </div>

            <div class="col-6">
              <q-input
                v-model.number="localConfig.max_tokens"
                label="Max Tokens"
                type="number"
                outlined
                dense
                min="100"
                max="8000"
                :rules="[val => val >= 100 && val <= 8000 || 'Max Tokens应在100-8000之间']"
              >
                <template v-slot:prepend>
                  <q-icon name="format_size" />
                </template>
              </q-input>
            </div>
          </div>

          <!-- R18内容选项 -->
          <div class="q-mt-md">
            <q-checkbox
              v-model="localConfig.nsfw_mode"
              label="解锁R18内容"
              color="orange"
            >
              <q-tooltip>
                启用后将允许生成成人内容和18+角色设定
              </q-tooltip>
            </q-checkbox>
          </div>
        </div>

        <!-- OpenAI 兼容配置 -->
        <div v-if="localConfig.api_type === 'openai'" class="openai-config">
          <div class="row q-gutter-md">
            <div class="col-12">
              <q-input
                v-model="localConfig.api_key"
                label="API Key *"
                type="password"
                outlined
                dense
                :rules="[val => !!val || 'API Key是必填项']"
              >
                <template v-slot:prepend>
                  <q-icon name="key" />
                </template>
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="localConfig.base_url"
                label="API Base URL *"
                outlined
                dense
                placeholder="如: https://api.openai.com/v1"
                :rules="[val => !!val || 'Base URL是必填项']"
              >
                <template v-slot:prepend>
                  <q-icon name="link" />
                </template>
              </q-input>
            </div>

            <div class="col-12">
              <q-input
                v-model="localConfig.model"
                label="模型名称 *"
                outlined
                dense
                placeholder="如: gpt-3.5-turbo, claude-3-sonnet-20240229"
                :rules="[val => !!val || '模型名称是必填项']"
              >
                <template v-slot:prepend>
                  <q-icon name="psychology" />
                </template>
              </q-input>
            </div>

            <div class="col-6">
              <q-input
                v-model.number="localConfig.temperature"
                label="Temperature"
                type="number"
                outlined
                dense
                step="0.1"
                min="0"
                max="2"
                :rules="[val => val >= 0 && val <= 2 || 'Temperature应在0-2之间']"
              >
                <template v-slot:prepend>
                  <q-icon name="thermostat" />
                </template>
              </q-input>
            </div>

            <div class="col-6">
              <q-input
                v-model.number="localConfig.max_tokens"
                label="Max Tokens"
                type="number"
                outlined
                dense
                min="100"
                max="8000"
                :rules="[val => val >= 100 && val <= 8000 || 'Max Tokens应在100-8000之间']"
              >
                <template v-slot:prepend>
                  <q-icon name="format_size" />
                </template>
              </q-input>
            </div>
          </div>

          <!-- R18内容选项 -->
          <div class="q-mt-md">
            <q-checkbox
              v-model="localConfig.nsfw_mode"
              label="解锁R18内容"
              color="orange"
            >
              <q-tooltip>
                启用后将允许生成成人内容和18+角色设定
              </q-tooltip>
            </q-checkbox>
          </div>
        </div>

        <!-- 配置状态 -->
        <div v-if="configStatus" class="q-mt-md">
          <q-banner
            :class="configStatus.success ? 'bg-green-1 text-green-8' : 'bg-red-1 text-red-8'"
            rounded
          >
            <template v-slot:avatar>
              <q-icon :name="configStatus.success ? 'check_circle' : 'error'" />
            </template>
            {{ configStatus.message }}
          </q-banner>
        </div>
      </q-card-section>

      <q-card-actions align="right" class="bg-grey-1">
        <q-btn
          flat
          label="取消"
          color="grey"
          @click="closeDialog"
        />
        <q-btn
          :loading="testing"
          label="测试连接"
          color="orange"
          @click="testConnection"
        />
        <q-btn
          :loading="saving"
          label="保存配置"
          color="primary"
          @click="saveConfig"
        />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

// Props
interface Props {
  modelValue: boolean;
  initialConfig?: ApiConfig;
}

const props = withDefaults(defineProps<Props>(), {
  initialConfig: () => ({
    api_type: 'openai',
    api_key: '',
    base_url: '',
    model: '',
    evaluator_model: '',
    temperature: 0.7,
    max_tokens: 4000,
    nsfw_mode: false
  })
});

// Emits
interface Emits {
  (e: 'update:modelValue', value: boolean): void;
  (e: 'config-saved', config: ApiConfig): void;
}

const emit = defineEmits<Emits>();

// Types
interface ApiConfig {
  api_type: 'gemini' | 'openai';
  api_key: string;
  base_url: string;
  model: string;
  evaluator_model?: string; // Gemini专用评估模型
  temperature: number;
  max_tokens: number;
  nsfw_mode: boolean;
}

// Reactive data
const showDialog = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const localConfig = ref<ApiConfig>({ ...props.initialConfig });
const configStatus = ref<{ success: boolean; message: string } | null>(null);
const testing = ref(false);
const saving = ref(false);

// Options
const apiTypeOptions = [
  { label: 'OpenAI 兼容 (推荐)', value: 'openai' },
  { label: 'Google Gemini', value: 'gemini' }
];

// Methods
function onApiTypeChange() {
  configStatus.value = null;
  if (localConfig.value.api_type === 'gemini') {
    // Reset OpenAI fields when switching to Gemini
    localConfig.value.api_key = '';
    localConfig.value.base_url = '';
    localConfig.value.model = '';
    localConfig.value.evaluator_model = '';
  } else if (localConfig.value.api_type === 'openai') {
    // Reset to empty OpenAI config - user must fill all fields
    localConfig.value.api_key = '';
    localConfig.value.base_url = '';
    localConfig.value.model = '';
    localConfig.value.evaluator_model = '';
  }
}

function closeDialog() {
  showDialog.value = false;
  configStatus.value = null;
}

async function testConnection() {
  testing.value = true;
  configStatus.value = null;

  try {
    if (localConfig.value.api_type === 'openai') {
      // Validate required fields
      if (!localConfig.value.api_key || !localConfig.value.base_url || !localConfig.value.model) {
        throw new Error('请填写所有必填字段');
      }

      // Simple test request (you can implement a test endpoint on the backend)
      const response = await fetch(`${localConfig.value.base_url}/models`, {
        headers: {
          'Authorization': `Bearer ${localConfig.value.api_key}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        configStatus.value = {
          success: true,
          message: '连接测试成功！'
        };
      } else {
        throw new Error(`连接失败: ${response.status} ${response.statusText}`);
      }
    } else if (localConfig.value.api_type === 'gemini') {
      // For Gemini, validate required fields
      if (!localConfig.value.api_key || !localConfig.value.model) {
        throw new Error('请填写所有必填字段');
      }

      configStatus.value = {
        success: true,
        message: 'Gemini配置已验证，保存后生效'
      };
    }
  } catch (error: unknown) {
    configStatus.value = {
      success: false,
      message: (error as Error).message || '连接测试失败'
    };
  } finally {
    testing.value = false;
  }
}

function saveConfig() {
  saving.value = true;

  try {
    // Validate configuration
    if (localConfig.value.api_type === 'openai') {
      if (!localConfig.value.api_key || !localConfig.value.base_url || !localConfig.value.model) {
        throw new Error('请填写所有必填字段');
      }
    } else if (localConfig.value.api_type === 'gemini') {
      if (!localConfig.value.api_key || !localConfig.value.model) {
        throw new Error('请填写所有必填字段');
      }
    }

    // Save to localStorage
    const configToSave = { ...localConfig.value };
    localStorage.setItem('api-config', JSON.stringify(configToSave));

    // Emit config
    emit('config-saved', configToSave);

    configStatus.value = {
      success: true,
      message: '配置已保存！'
    };

    // Close dialog after a short delay
    setTimeout(() => {
      closeDialog();
    }, 1000);

  } catch (error: unknown) {
    configStatus.value = {
      success: false,
      message: (error as Error).message || '保存配置失败'
    };
  } finally {
    saving.value = false;
  }
}

// Watch for prop changes
watch(() => props.initialConfig, (newConfig) => {
  localConfig.value = { ...newConfig };
}, { deep: true });
</script>

<style scoped>
.api-config-card {
  min-width: 500px;
}

.gemini-config, .openai-config {
  margin-top: 16px;
}
</style>
