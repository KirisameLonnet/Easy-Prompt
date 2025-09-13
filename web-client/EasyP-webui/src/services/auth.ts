/**
 * 用户认证服务
 */
import { ref } from 'vue'

export interface User {
  id: string
  username: string
  email: string
  role: string
  status: string
  created_at: string
  updated_at: string
  last_login?: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface ApiConfig {
  api_type: string
  api_key: string
  base_url: string
  model: string
  evaluator_model?: string
  temperature: number
  max_tokens: number
  nsfw_mode: boolean
}

class AuthService {
  private baseUrl = 'http://127.0.0.1:8000'
  private tokenKey = 'auth_token'
  private userKey = 'user_info'

  // 响应式状态
  public isAuthenticated = ref(false)
  public currentUser = ref<User | null>(null)
  public token = ref<string | null>(null)

  constructor() {
    this.loadStoredAuth()
  }

  /**
   * 加载存储的认证信息
   */
  private loadStoredAuth(): void {
    const storedToken = localStorage.getItem(this.tokenKey)
    const storedUser = localStorage.getItem(this.userKey)

    if (storedToken && storedUser) {
      this.token.value = storedToken
      this.currentUser.value = JSON.parse(storedUser)
      this.isAuthenticated.value = true
    }
  }

  /**
   * 保存认证信息到本地存储
   */
  private saveAuth(token: string, user: User | null): void {
    localStorage.setItem(this.tokenKey, token)
    if (user) {
      localStorage.setItem(this.userKey, JSON.stringify(user))
      this.currentUser.value = user
    }
    this.token.value = token
    this.isAuthenticated.value = true
  }

  /**
   * 清除认证信息
   */
  private clearAuth(): void {
    localStorage.removeItem(this.tokenKey)
    localStorage.removeItem(this.userKey)
    this.token.value = null
    this.currentUser.value = null
    this.isAuthenticated.value = false
  }

  /**
   * 用户注册
   */
  async register(userData: RegisterRequest): Promise<User> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '注册失败')
      }

      const user = await response.json()
      return user
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  /**
   * 用户登录
   */
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '登录失败')
      }

      const tokenData = await response.json()

      // 保存令牌，稍后获取用户信息
      this.saveAuth(tokenData.access_token, null)

      // 尝试获取用户信息（可选）
      try {
        const user = await this.getCurrentUser()
        this.saveAuth(tokenData.access_token, user)
      } catch (error) {
        console.warn('登录成功但获取用户信息失败，将在需要时重试:', error)
        // 不抛出错误，登录仍然成功
      }

      return tokenData
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<User> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      console.log('正在获取用户信息，令牌:', this.token.value.substring(0, 20) + '...')
      const response = await fetch(`${this.baseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
      })

      console.log('用户信息响应状态:', response.status)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('获取用户信息失败:', response.status, errorText)
        if (response.status === 401) {
          this.clearAuth()
          throw new Error('认证已过期，请重新登录')
        }
        throw new Error(`获取用户信息失败: ${response.status} ${errorText}`)
      }

      const user = await response.json()
      console.log('获取到用户信息:', user)
      return user
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 用户登出
   */
  async logout(): Promise<void> {
    try {
      if (this.token.value) {
        await fetch(`${this.baseUrl}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.token.value}`,
          },
        })
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      this.clearAuth()
    }
  }

  /**
   * 验证令牌有效性
   */
  async verifyToken(): Promise<boolean> {
    if (!this.token.value) {
      return false
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/verify-token`, {
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        this.currentUser.value = data.user
        return true
      } else {
        this.clearAuth()
        return false
      }
    } catch (error) {
      console.error('验证令牌失败:', error)
      this.clearAuth()
      return false
    }
  }

  /**
   * 延迟获取用户信息（用于登录后）
   */
  async refreshUserInfo(): Promise<void> {
    if (!this.token.value) {
      return
    }

    try {
      const user = await this.getCurrentUser()
      this.currentUser.value = user
      localStorage.setItem(this.userKey, JSON.stringify(user))
    } catch (error) {
      console.warn('刷新用户信息失败:', error)
    }
  }

  /**
   * 获取用户API配置
   */
  async getApiConfig(): Promise<ApiConfig | null> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/user/api-config`, {
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
        },
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null // 没有配置
        }
        throw new Error('获取API配置失败')
      }

      const data = await response.json()
      return data.config
    } catch (error) {
      console.error('获取API配置失败:', error)
      throw error
    }
  }

  /**
   * 保存用户API配置
   */
  async saveApiConfig(config: ApiConfig): Promise<void> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/user/api-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token.value}`,
        },
        body: JSON.stringify(config),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '保存API配置失败')
      }
    } catch (error) {
      console.error('保存API配置失败:', error)
      throw error
    }
  }

  /**
   * 更新用户API配置
   */
  async updateApiConfig(config: ApiConfig): Promise<void> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/user/api-config`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.token.value}`,
        },
        body: JSON.stringify(config),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '更新API配置失败')
      }
    } catch (error) {
      console.error('更新API配置失败:', error)
      throw error
    }
  }

  /**
   * 测试API配置
   */
  async testApiConfig(): Promise<boolean> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/user/test-api-config`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '测试API配置失败')
      }

      const data = await response.json()
      return data.message.includes('成功')
    } catch (error) {
      console.error('测试API配置失败:', error)
      throw error
    }
  }

  /**
   * 获取认证头
   */
  getAuthHeaders(): Record<string, string> {
    if (!this.token.value) {
      return {}
    }
    return {
      'Authorization': `Bearer ${this.token.value}`,
    }
  }
}

// 创建全局实例
export const authService = new AuthService()

// 类型已经在上面通过export interface导出了，这里不需要重复导出
