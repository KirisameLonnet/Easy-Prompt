/**
 * Supabase认证服务
 */
import { ref } from 'vue'

export interface SupabaseUser {
  id: string
  email: string
  username?: string
  full_name?: string
  avatar_url?: string
  created_at: string
  updated_at: string
  last_sign_in_at?: string
  email_confirmed_at?: string
  phone?: string
  role: string
  status: string
}

export interface AuthResponse {
  user: SupabaseUser
  access_token: string
  refresh_token: string
  expires_in: number
  token_type: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  username: string
  full_name?: string
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

class SupabaseAuthService {
  private baseUrl = 'http://127.0.0.1:8000'
  private tokenKey = 'supabase_access_token'
  private refreshTokenKey = 'supabase_refresh_token'
  private userKey = 'supabase_user_info'

  // 响应式状态
  public isAuthenticated = ref(false)
  public currentUser = ref<SupabaseUser | null>(null)
  public token = ref<string | null>(null)

  constructor() {
    this.initializeAuth()
  }

  /**
   * 初始化认证状态
   */
  private initializeAuth(): void {
    const token = localStorage.getItem(this.tokenKey)
    const userStr = localStorage.getItem(this.userKey)

    if (token && userStr) {
      try {
        this.token.value = token
        this.currentUser.value = JSON.parse(userStr)
        this.isAuthenticated.value = true
      } catch (error) {
        console.error('初始化认证状态失败:', error)
        this.clearAuth()
      }
    }
  }

  /**
   * 保存认证信息到本地存储
   */
  private saveAuth(authResponse: AuthResponse): void {
    localStorage.setItem(this.tokenKey, authResponse.access_token)
    localStorage.setItem(this.refreshTokenKey, authResponse.refresh_token)
    localStorage.setItem(this.userKey, JSON.stringify(authResponse.user))

    this.token.value = authResponse.access_token
    this.currentUser.value = authResponse.user
    this.isAuthenticated.value = true
  }

  /**
   * 清除认证信息
   */
  private clearAuth(): void {
    localStorage.removeItem(this.tokenKey)
    localStorage.removeItem(this.refreshTokenKey)
    localStorage.removeItem(this.userKey)

    this.token.value = null
    this.currentUser.value = null
    this.isAuthenticated.value = false
  }

  /**
   * 用户注册
   */
  async register(registerData: RegisterRequest): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(registerData)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '注册失败')
      }

      const authResponse = await response.json()
      this.saveAuth(authResponse)
      return authResponse
    } catch (error) {
      console.error('注册失败:', error)
      throw error
    }
  }

  /**
   * 用户登录
   */
  async login(loginData: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData)
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '登录失败')
      }

      const authResponse = await response.json()
      this.saveAuth(authResponse)
      return authResponse
    } catch (error) {
      console.error('登录失败:', error)
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
   * 获取当前用户信息
   */
  async getCurrentUser(): Promise<SupabaseUser> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 401) {
          this.clearAuth()
          throw new Error('认证已过期，请重新登录')
        }
        throw new Error('获取用户信息失败')
      }

      const user = await response.json()
      this.currentUser.value = user
      localStorage.setItem(this.userKey, JSON.stringify(user))
      return user
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 刷新访问令牌
   */
  async refreshToken(): Promise<AuthResponse> {
    const refreshToken = localStorage.getItem(this.refreshTokenKey)
    if (!refreshToken) {
      throw new Error('没有刷新令牌')
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      })

      if (!response.ok) {
        throw new Error('令牌刷新失败')
      }

      const authResponse = await response.json()
      this.saveAuth(authResponse)
      return authResponse
    } catch (error) {
      console.error('令牌刷新失败:', error)
      this.clearAuth()
      throw error
    }
  }

  /**
   * 重置密码
   */
  async resetPassword(email: string): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/auth/reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '密码重置失败')
      }
    } catch (error) {
      console.error('密码重置失败:', error)
      throw error
    }
  }

  /**
   * 更新密码
   */
  async updatePassword(password: string, newPassword: string): Promise<void> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/update-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password, new_password: newPassword })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '密码更新失败')
      }
    } catch (error) {
      console.error('密码更新失败:', error)
      throw error
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
      const response = await fetch(`${this.baseUrl}/auth/api-config`, {
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
      const response = await fetch(`${this.baseUrl}/auth/api-config`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
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
      const response = await fetch(`${this.baseUrl}/auth/api-config`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
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
   * 删除用户API配置
   */
  async deleteApiConfig(): Promise<void> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/api-config`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
        },
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || '删除API配置失败')
      }
    } catch (error) {
      console.error('删除API配置失败:', error)
      throw error
    }
  }

  /**
   * 测试API配置
   */
  async testApiConfig(config: ApiConfig): Promise<{ success: boolean; message: string }> {
    if (!this.token.value) {
      throw new Error('未登录')
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/api-config/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.token.value}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      })

      const result = await response.json()
      return result
    } catch (error) {
      console.error('测试API配置失败:', error)
      return {
        success: false,
        message: `测试失败: ${error instanceof Error ? error.message : '未知错误'}`
      }
    }
  }
}

// 创建全局实例
export const supabaseAuthService = new SupabaseAuthService()

// 导出类型
export type { SupabaseUser, AuthResponse, LoginRequest, RegisterRequest, ApiConfig }
