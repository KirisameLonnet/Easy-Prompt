<template>
  <div class="user-info">
    <q-btn-dropdown
      flat
      :label="user?.username || '用户'"
      icon="person"
      color="primary"
    >
      <q-list>
        <q-item-label header>用户信息</q-item-label>
        <q-item>
          <q-item-section>
            <q-item-label>用户名</q-item-label>
            <q-item-label caption>{{ user?.username }}</q-item-label>
          </q-item-section>
        </q-item>
        <q-item>
          <q-item-section>
            <q-item-label>邮箱</q-item-label>
            <q-item-label caption>{{ user?.email }}</q-item-label>
          </q-item-section>
        </q-item>
        <q-item>
          <q-item-section>
            <q-item-label>角色</q-item-label>
            <q-item-label caption>{{ getRoleText(user?.role) }}</q-item-label>
          </q-item-section>
        </q-item>
        <q-separator />
        <q-item clickable v-close-popup @click="handleLogout">
          <q-item-section avatar>
            <q-icon name="logout" />
          </q-item-section>
          <q-item-section>
            <q-item-label>退出登录</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-btn-dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useQuasar } from 'quasar'
import { authService } from '../services/auth'

interface Emits {
  (e: 'logout'): void
}

const emit = defineEmits<Emits>()
const $q = useQuasar()

// 计算属性
const user = computed(() => authService.currentUser.value)

// 获取角色文本
const getRoleText = (role?: string) => {
  const roleMap: Record<string, string> = {
    'user': '普通用户',
    'admin': '管理员',
    'premium': '高级用户'
  }
  return roleMap[role || 'user'] || '未知'
}

// 处理登出
const handleLogout = async () => {
  try {
    await authService.logout()
    if ($q && $q.notify) {
      $q.notify({
        type: 'positive',
        message: '已退出登录',
        position: 'top'
      })
    }
    emit('logout')
  } catch (error) {
    console.error('登出失败:', error)
    if ($q && $q.notify) {
      $q.notify({
        type: 'negative',
        message: '登出失败',
        position: 'top'
      })
    }
  }
}
</script>

<style scoped>
.user-info {
  display: flex;
  align-items: center;
}
</style>
