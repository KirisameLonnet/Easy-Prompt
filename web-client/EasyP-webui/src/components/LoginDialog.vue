<template>
  <q-dialog v-model="show" persistent>
    <q-card style="min-width: 400px">
      <q-card-section class="row items-center q-pb-none">
        <div class="text-h6">用户登录</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </q-card-section>

      <q-card-section>
        <q-tabs v-model="activeTab" class="text-grey" active-color="primary" indicator-color="primary" align="justify" narrow-indicator>
          <q-tab name="login" label="登录" />
          <q-tab name="register" label="注册" />
        </q-tabs>

        <q-separator />

        <q-tab-panels v-model="activeTab" animated>
          <!-- 登录面板 -->
          <q-tab-panel name="login">
            <q-form @submit="handleLogin" class="q-gutter-md">
              <q-input
                v-model="loginForm.username"
                label="用户名或邮箱"
                :rules="[val => !!val || '请输入用户名或邮箱']"
                outlined
                dense
              />
              <q-input
                v-model="loginForm.password"
                label="密码"
                type="password"
                :rules="[val => !!val || '请输入密码']"
                outlined
                dense
              />
              <div class="row q-gutter-sm">
                <q-btn
                  type="submit"
                  label="登录"
                  color="primary"
                  :loading="loading"
                  :disable="loading"
                  class="col"
                />
                <q-btn
                  label="取消"
                  color="grey"
                  @click="closeDialog"
                  class="col"
                />
              </div>
            </q-form>
          </q-tab-panel>

          <!-- 注册面板 -->
          <q-tab-panel name="register">
            <q-form @submit="handleRegister" class="q-gutter-md">
              <q-input
                v-model="registerForm.username"
                label="用户名"
                :rules="[
                  val => !!val || '请输入用户名',
                  val => val.length >= 3 || '用户名至少3个字符',
                  val => val.length <= 50 || '用户名最多50个字符'
                ]"
                outlined
                dense
              />
              <q-input
                v-model="registerForm.email"
                label="邮箱"
                type="email"
                :rules="[
                  val => !!val || '请输入邮箱',
                  val => /.+@.+\..+/.test(val) || '请输入有效的邮箱地址'
                ]"
                outlined
                dense
              />
              <q-input
                v-model="registerForm.password"
                label="密码"
                type="password"
                :rules="[
                  val => !!val || '请输入密码',
                  val => val.length >= 6 || '密码至少6个字符'
                ]"
                outlined
                dense
              />
              <q-input
                v-model="registerForm.confirmPassword"
                label="确认密码"
                type="password"
                :rules="[
                  val => !!val || '请确认密码',
                  val => val === registerForm.password || '两次输入的密码不一致'
                ]"
                outlined
                dense
              />
              <div class="row q-gutter-sm">
                <q-btn
                  type="submit"
                  label="注册"
                  color="primary"
                  :loading="loading"
                  :disable="loading"
                  class="col"
                />
                <q-btn
                  label="取消"
                  color="grey"
                  @click="closeDialog"
                  class="col"
                />
              </div>
            </q-form>
          </q-tab-panel>
        </q-tab-panels>
      </q-card-section>

      <q-card-section v-if="errorMessage" class="q-pt-none">
        <q-banner class="bg-negative text-white" rounded>
          {{ errorMessage }}
        </q-banner>
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuasar } from 'quasar'
import { authService, type LoginRequest, type RegisterRequest } from '../services/auth'

interface Props {
  modelValue: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'login-success'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const $q = useQuasar()

// 响应式数据
const show = ref(props.modelValue)
const activeTab = ref('login')
const loading = ref(false)
const errorMessage = ref('')

// 表单数据
const loginForm = ref<LoginRequest>({
  username: '',
  password: ''
})

const registerForm = ref<RegisterRequest & { confirmPassword: string }>({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 监听props变化
watch(() => props.modelValue, (newVal) => {
  show.value = newVal
  if (newVal) {
    resetForms()
  }
})

// 监听show变化
watch(show, (newVal) => {
  emit('update:modelValue', newVal)
})

// 重置表单
const resetForms = () => {
  loginForm.value = { username: '', password: '' }
  registerForm.value = { username: '', email: '', password: '', confirmPassword: '' }
  errorMessage.value = ''
  activeTab.value = 'login'
}

// 关闭对话框
const closeDialog = () => {
  show.value = false
}

// 处理登录
const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    await authService.login(loginForm.value)
    if ($q && $q.notify) {
      $q.notify({
        type: 'positive',
        message: '登录成功！',
        position: 'top'
      })
    }
    emit('login-success')
    closeDialog()
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : '登录失败'
  } finally {
    loading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { confirmPassword, ...registerData } = registerForm.value
    await authService.register(registerData)

    if ($q && $q.notify) {
      $q.notify({
        type: 'positive',
        message: '注册成功！请登录',
        position: 'top'
      })
    }

    // 切换到登录面板
    activeTab.value = 'login'
    resetForms()
  } catch (error: unknown) {
    errorMessage.value = error instanceof Error ? error.message : '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.q-card {
  max-width: 500px;
}
</style>
