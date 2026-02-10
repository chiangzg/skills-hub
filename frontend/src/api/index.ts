/**
 * API 客户端
 */
import type {
  ApiResponse,
  User,
  LoginResponse,
  ChangePasswordRequest,
  Repository,
  RepositoryCreate,
  RepositoryUpdate,
  SyncResponse,
  WebhookConfig,
  Category,
  CategoryTree,
  AssignCategoriesRequest,
  CategoryCreate,
  CategoryUpdate,
  Skill,
  SkillListParams,
  WebhookLog,
  SyncStatus,
  CreateUserRequest,
  UpdateUserRequest,
  ResetPasswordRequest
} from '../types/api'

const API_BASE = '/api'

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

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  async put<T>(endpoint: string, body?: unknown): Promise<T> {
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
  async login(username: string, password: string): Promise<LoginResponse> {
    return api.post<LoginResponse>('/auth/login', { username, password })
  },
  async getMe(): Promise<User> {
    return api.get<User>('/auth/me')
  },
  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    return api.post<void>('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    } as ChangePasswordRequest)
  }
}

// 仓库 API
export const repositoryApi = {
  async list(): Promise<Repository[]> {
    return api.get<Repository[]>('/admin/repositories')
  },
  async create(data: RepositoryCreate): Promise<Repository> {
    return api.post<Repository>('/admin/repositories', data)
  },
  async get(id: number): Promise<Repository> {
    return api.get<Repository>(`/admin/repositories/${id}`)
  },
  async update(id: number, data: RepositoryUpdate): Promise<Repository> {
    return api.put<Repository>(`/admin/repositories/${id}`, data)
  },
  async delete(id: number): Promise<void> {
    return api.delete<void>(`/admin/repositories/${id}`)
  },
  async sync(id: number): Promise<SyncResponse> {
    return api.post<SyncResponse>(`/admin/repositories/${id}/sync`)
  },
  async configureWebhook(id: number, enabled: boolean, secret?: string): Promise<{ message: string; enabled: boolean }> {
    return api.post<{ message: string; enabled: boolean }>(`/admin/repositories/${id}/webhook`, { enabled, secret } as WebhookConfig)
  }
}

// 分类 API
export const categoryApi = {
  async getTree(): Promise<CategoryTree[]> {
    return api.get<CategoryTree[]>('/admin/categories/tree')
  },
  async list(): Promise<Category[]> {
    return api.get<Category[]>('/admin/categories')
  },
  async create(data: CategoryCreate): Promise<Category> {
    return api.post<Category>('/admin/categories', data)
  },
  async update(id: number, data: CategoryUpdate): Promise<Category> {
    return api.put<Category>(`/admin/categories/${id}`, data)
  },
  async delete(id: number): Promise<void> {
    return api.delete<void>(`/admin/categories/${id}`)
  },
  async assignSkill(skillId: number, categoryIds: number[]): Promise<void> {
    return api.post<void>(`/admin/categories/skills/${skillId}/categories`, { category_ids: categoryIds } as AssignCategoriesRequest)
  },
  async addSkill(categoryId: number, skillId: number): Promise<void> {
    return api.post<void>(`/admin/categories/${categoryId}/skills/${skillId}`)
  },
  async removeSkill(categoryId: number, skillId: number): Promise<void> {
    return api.delete<void>(`/admin/categories/${categoryId}/skills/${skillId}`)
  }
}

// Skill API
export const skillApi = {
  async list(params: SkillListParams = {}): Promise<PaginatedResponse<Skill>> {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        searchParams.append(key, String(value))
      }
    })
    const query = searchParams.toString()
    return api.get<PaginatedResponse<Skill>>(`/skills${query ? `?${query}` : ''}`)
  },
  async get(id: number): Promise<Skill> {
    return api.get<Skill>(`/skills/${id}`)
  },
  async getPending(): Promise<Skill[]> {
    return api.get<Skill[]>('/skills/sync/pending')
  }
}

// 用户管理 API
export const userApi = {
  async list(): Promise<User[]> {
    return api.get<User[]>('/admin/users')
  },
  async create(data: CreateUserRequest): Promise<User> {
    return api.post<User>('/admin/users', data)
  },
  async update(id: number, data: UpdateUserRequest): Promise<User> {
    return api.put<User>(`/admin/users/${id}`, data)
  },
  async delete(id: number): Promise<void> {
    return api.delete<void>(`/admin/users/${id}`)
  },
  async resetPassword(id: number, newPassword: string): Promise<void> {
    return api.post<void>(`/admin/users/${id}/reset-password`, { new_password: newPassword } as ResetPasswordRequest)
  }
}

// 同步 API
export const syncApi = {
  async syncRepo(id: number): Promise<SyncResponse> {
    return api.post<SyncResponse>(`/admin/sync/${id}`)
  },
  async syncAll(): Promise<SyncResponse> {
    return api.post<SyncResponse>('/admin/sync/all')
  },
  async getStatus(): Promise<SyncStatus> {
    return api.get<SyncStatus>('/admin/sync/status')
  }
}

// Webhook API
export const webhookApi = {
  async getLogs(repoId?: number): Promise<WebhookLog[]> {
    const query = repoId ? `?repository_id=${repoId}` : ''
    return api.get<WebhookLog[]>(`/webhooks/logs${query}`)
  }
}
