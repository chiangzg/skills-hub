/**
 * API 客户端
 */

const API_BASE = '/api'

interface ApiResponse<T> {
  error?: {
    code: string
    message: string
    details?: any
    timestamp: string
  }
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
    // 从 localStorage 读取 token
    this.token = localStorage.getItem('token')
  }

  setToken(token: string) {
    this.token = token
    localStorage.setItem('token', token)
  }

  clearToken() {
    this.token = null
    localStorage.removeItem('token')
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers
    })

    // 处理 204 No Content 响应（如 DELETE 请求）
    if (response.status === 204) {
      return undefined as T
    }

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.error?.message || 'Request failed')
    }

    return data as T
  }

  async get<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'GET' })
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  async put<T>(endpoint: string, body?: any): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}

export const api = new ApiClient()

// 认证 API
export const authApi = {
  async login(username: string, password: string) {
    return api.post('/auth/login', { username, password })
  },
  async getMe() {
    return api.get('/auth/me')
  },
  async changePassword(oldPassword: string, newPassword: string) {
    return api.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
  }
}

// 仓库 API
export const repositoryApi = {
  async list() {
    return api.get('/admin/repositories')
  },
  async create(data: any) {
    return api.post('/admin/repositories', data)
  },
  async get(id: number) {
    return api.get(`/admin/repositories/${id}`)
  },
  async update(id: number, data: any) {
    return api.put(`/admin/repositories/${id}`, data)
  },
  async delete(id: number) {
    return api.delete(`/admin/repositories/${id}`)
  },
  async sync(id: number) {
    return api.post(`/admin/repositories/${id}/sync`)
  },
  async configureWebhook(id: number, enabled: boolean, secret?: string) {
    return api.post(`/admin/repositories/${id}/webhook`, { enabled, secret })
  }
}

// 分类 API
export const categoryApi = {
  async getTree() {
    return api.get('/admin/categories/tree')
  },
  async list() {
    return api.get('/admin/categories')
  },
  async create(data: any) {
    return api.post('/admin/categories', data)
  },
  async update(id: number, data: any) {
    return api.put(`/admin/categories/${id}`, data)
  },
  async delete(id: number) {
    return api.delete(`/admin/categories/${id}`)
  },
  async assignSkill(skillId: number, categoryIds: number[]) {
    return api.post(`/admin/categories/skills/${skillId}/categories`, { category_ids: categoryIds })
  },
  async addSkill(categoryId: number, skillId: number) {
    return api.post(`/admin/categories/${categoryId}/skills/${skillId}`)
  },
  async removeSkill(categoryId: number, skillId: number) {
    return api.delete(`/admin/categories/${categoryId}/skills/${skillId}`)
  }
}

// Skill API
export const skillApi = {
  async list(params: {
    keyword?: string
    category_id?: number
    repository_id?: number
    page?: number
    page_size?: number
    sort_by?: string
    sort_order?: string
  } = {}) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value))
      }
    })
    const query = searchParams.toString()
    return api.get(`/skills${query ? `?${query}` : ''}`)
  },
  async get(id: number) {
    return api.get(`/skills/${id}`)
  },
  async getPending() {
    return api.get('/skills/sync/pending')
  }
}

// 用户管理 API
export const userApi = {
  async list() {
    return api.get('/admin/users')
  },
  async create(data: any) {
    return api.post('/admin/users', data)
  },
  async update(id: number, data: any) {
    return api.put(`/admin/users/${id}`, data)
  },
  async delete(id: number) {
    return api.delete(`/admin/users/${id}`)
  },
  async resetPassword(id: number, newPassword: string) {
    return api.post(`/admin/users/${id}/reset-password`, { new_password: newPassword })
  }
}

// 同步 API
export const syncApi = {
  async syncRepo(id: number) {
    return api.post(`/admin/sync/${id}`)
  },
  async syncAll() {
    return api.post('/admin/sync/all')
  },
  async getStatus() {
    return api.get('/admin/sync/status')
  }
}

// Webhook API
export const webhookApi = {
  async getLogs(repoId?: number) {
    const query = repoId ? `?repository_id=${repoId}` : ''
    return api.get(`/webhooks/logs${query}`)
  }
}
