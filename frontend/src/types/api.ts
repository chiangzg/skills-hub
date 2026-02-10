/**
 * API 类型定义
 */

// 通用 API 响应格式
export interface ApiResponse<T = any> {
  error?: {
    code: string
    message: string
    details?: T
    timestamp: string
  }
}

// 分页响应
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

// 用户相关
export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

// 仓库相关
export enum RepositoryType {
  GITHUB = 'github',
  GITLAB = 'gitlab'
}

export interface Repository {
  id: number
  type: RepositoryType
  owner: string
  name: string
  branch: string
  gitlab_url?: string
  access_token?: string
  enabled: boolean
  webhook_enabled: boolean
  full_name: string
  skill_count?: number
  created_at: string
  updated_at: string
}

export interface RepositoryCreate {
  type: RepositoryType
  owner: string
  name: string
  branch: string
  gitlab_url?: string
  access_token?: string
}

export interface RepositoryUpdate {
  branch?: string
  enabled?: boolean
  access_token?: string
  gitlab_url?: string
}

export interface SyncResponse {
  success: boolean
  message: string
  skills_added: number
  skills_updated: number
  skills_removed: number
}

export interface WebhookConfig {
  enabled: boolean
  secret?: string
}

// 分类相关
export interface Category {
  id: number
  name: string
  slug: string
  description?: string
  icon?: string
  parent_id?: number
  children?: Category[]
  skill_count?: number
  created_at: string
  updated_at: string
}

export interface CategoryCreate {
  name: string
  slug?: string
  description?: string
  icon?: string
  parent_id?: number
}

export interface CategoryUpdate {
  name?: string
  slug?: string
  description?: string
  icon?: string
}

export interface CategoryTree {
  id: number
  name: string
  slug: string
  description?: string
  icon?: string
  children?: CategoryTree[]
  skill_count?: number
}

export interface AssignCategoriesRequest {
  category_ids: number[]
}

// 技能相关
export interface Skill {
  id: number
  name: string
  description?: string
  content?: string
  directory: string
  readme_url?: string
  tags: string[]
  technologies?: string[]
  repository?: {
    id: number
    full_name: string
    type: string
  }
  categories?: Category[]
  created_at: string
  updated_at: string
}

export interface SkillListParams {
  keyword?: string
  category_id?: number
  repository_id?: number
  page?: number
  page_size?: number
  sort_by?: string
  sort_order?: 'asc' | 'desc'
}

// Webhook 相关
export interface WebhookLog {
  id: number
  repository_id: number
  event_type: string
  status: string
  error_message?: string
  triggered_at: string
  processed_at?: string
  has_payload: boolean
}

// 同步相关
export interface SyncStatus {
  is_syncing: boolean
  current_repository?: string
  completed: number
  total: number
}

// 用户管理相关
export interface CreateUserRequest {
  username: string
  password: string
  role?: 'admin' | 'user'
}

export interface UpdateUserRequest {
  password?: string
  role?: 'admin' | 'user'
  is_active?: boolean
}

export interface ResetPasswordRequest {
  new_password: string
}
