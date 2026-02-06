<template>
  <div class="admin-dashboard">
    <!-- 顶部导航栏 -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="header-left">
          <div class="logo-section">
            <div class="logo-icon">{ }</div>
            <h1 class="dashboard-title">管理控制台</h1>
          </div>
        </div>
        
        <div class="header-right">
          <div class="user-info">
            <span class="username">{{ username }}</span>
            <span class="role-badge" :class="userRole">{{ userRole === 'admin' ? '管理员' : '普通用户' }}</span>
          </div>
          <button @click="logout" class="logout-button">
            <span class="button-icon">🚪</span>
            退出登录
          </button>
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="dashboard-main">
      <div class="main-content">
        <!-- 标签页导航 -->
        <div class="tabs-navigation">
          <div class="tabs-container">
            <button
              :class="['tab-button', { active: activeTab === 'repositories' }]"
              @click="activeTab = 'repositories'"
            >
              <div class="tab-icon-wrapper">
                <span class="tab-icon">📦</span>
              </div>
              <div class="tab-info">
                <span class="tab-label">仓库管理</span>
                <span class="tab-count">{{ repoCount }}</span>
              </div>
            </button>

            <button
              :class="['tab-button', { active: activeTab === 'categories' }]"
              @click="activeTab = 'categories'"
            >
              <div class="tab-icon-wrapper">
                <span class="tab-icon">📂</span>
              </div>
              <div class="tab-info">
                <span class="tab-label">分类管理</span>
                <span class="tab-count">{{ categoryCount }}</span>
              </div>
            </button>

            <button
              v-if="isAdmin"
              :class="['tab-button', { active: activeTab === 'users' }]"
              @click="activeTab = 'users'"
            >
              <div class="tab-icon-wrapper">
                <span class="tab-icon">👥</span>
              </div>
              <div class="tab-info">
                <span class="tab-label">用户管理</span>
                <span class="tab-count">{{ userCount }}</span>
              </div>
            </button>

            <button
              v-if="isAdmin"
              :class="['tab-button', { active: activeTab === 'skill-categories' }]"
              @click="activeTab = 'skill-categories'"
            >
              <div class="tab-icon-wrapper">
                <span class="tab-icon">⚙️</span>
              </div>
              <div class="tab-info">
                <span class="tab-label">技能分类管理</span>
                <span class="tab-count">{{ skillCategoryCount }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 标签页内容 -->
        <div class="tab-content">
          <div v-show="activeTab === 'repositories'" class="content-section">
            <RepositoryPanel @data-change="handleRepoChange" />
          </div>
          
          <div v-show="activeTab === 'categories'" class="content-section">
            <CategoryPanel @data-change="handleCategoryChange" />
          </div>
          
          <div v-show="activeTab === 'users'" class="content-section">
            <UserPanel v-if="isAdmin" @data-change="handleUserChange" />
          </div>
          
          <div v-show="activeTab === 'skill-categories'" class="content-section">
            <SkillCategoryManager />
          </div>
        </div>
      </div>
    </div>

    <!-- 底部状态栏 -->
    <footer class="dashboard-footer">
      <div class="footer-content">
        <div class="status-indicators">
          <div class="status-item">
            <span class="status-dot online"></span>
            <span class="status-text">系统在线</span>
          </div>
          <div class="status-item">
            <span class="status-dot syncing" v-if="isSyncing"></span>
            <span class="status-text">{{ isSyncing ? '同步中...' : '就绪' }}</span>
          </div>
        </div>
        <div class="version-info">
          技能中心管理后台 v1.0
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import RepositoryPanel from '../../components/admin/RepositoryPanel.vue'
import CategoryPanel from '../../components/admin/CategoryPanel.vue'
import UserPanel from '../../components/admin/UserPanel.vue'
import SkillCategoryManager from '../../components/admin/SkillCategoryManager.vue'
import { api } from '../../api'

const router = useRouter()
const activeTab = ref('repositories')
const username = ref(localStorage.getItem('username') || '')
const userRole = ref(localStorage.getItem('userRole') || 'user')
const isAdmin = computed(() => userRole.value === 'admin')

// 数据统计
const repoCount = ref(0)
const categoryCount = ref(0)
const userCount = ref(0)
const skillCategoryCount = ref(0)
const isSyncing = ref(false)

onMounted(async () => {
  await loadDataCounts()
})

async function loadDataCounts() {
  try {
    // 并行加载统计数据
    const [repos, categories, users, skills] = await Promise.all([
      api.get('/admin/repositories').catch(() => []),
      api.get('/admin/categories').catch(() => []),
      isAdmin.value ? api.get('/admin/users').catch(() => []) : Promise.resolve([]),
      api.get('/skills?page_size=1').catch(() => { total: 0 })
    ])

    repoCount.value = Array.isArray(repos) ? repos.length : 0
    categoryCount.value = Array.isArray(categories) ? categories.length : 0
    userCount.value = Array.isArray(users) ? users.length : 0
    skillCategoryCount.value = skills.total || 0
  } catch (e) {
    console.error('Failed to load data counts:', e)
  }
}

function handleRepoChange() {
  loadDataCounts()
}

function handleCategoryChange() {
  loadDataCounts()
}

function handleUserChange() {
  loadDataCounts()
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userRole')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.admin-dashboard {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  display: flex;
  flex-direction: column;
}

.dashboard-header {
  background: rgba(21, 22, 34, 0.9);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-light);
  padding: 1rem 2rem;
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-icon {
  font-size: 1.8rem;
  font-weight: bold;
  color: var(--brand-blue);
}

.dashboard-title {
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.username {
  color: var(--text-primary);
  font-weight: 500;
}

.role-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
}

.role-badge.admin {
  background: rgba(247, 118, 142, 0.2);
  color: var(--brand-red);
}

.role-badge.user {
  background: rgba(122, 162, 247, 0.2);
  color: var(--brand-blue);
}

.logout-button {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.logout-button:hover {
  border-color: var(--brand-red);
  color: var(--brand-red);
  background: rgba(247, 118, 142, 0.1);
}

.button-icon {
  font-size: 1.1rem;
}

.dashboard-main {
  flex: 1;
  padding: 2rem;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
}

.tabs-navigation {
  margin-bottom: 2rem;
}

.tabs-container {
  display: flex;
  gap: 1rem;
}

.tab-button {
  flex: 1;
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  padding: 1.25rem;
  border-radius: 12px;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  gap: 1rem;
  color: var(--text-secondary);
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.tab-button:hover {
  border-color: var(--brand-blue);
  background: rgba(26, 27, 38, 0.9);
}

.tab-button.active {
  border-color: var(--brand-blue);
  background: rgba(122, 162, 247, 0.15);
  box-shadow: 0 0 0 1px var(--brand-blue);
}

.tab-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tab-button.active .tab-icon-wrapper {
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-cyan));
}

.tab-icon {
  font-size: 1.5rem;
}

.tab-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.25rem;
  flex: 1;
}

.tab-label {
  font-size: 1rem;
  color: var(--text-primary);
}

.tab-count {
  background: rgba(122, 162, 247, 0.2);
  color: var(--brand-blue);
  padding: 0.2rem 0.6rem;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
}

.tab-button.active .tab-count {
  background: rgba(122, 162, 247, 0.3);
}

.tab-content {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
  min-height: 500px;
}

.content-section {
  height: 100%;
}

.dashboard-footer {
  background: rgba(21, 22, 34, 0.9);
  backdrop-filter: blur(10px);
  border-top: 1px solid var(--border-light);
  padding: 1rem 2rem;
}

.footer-content {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicators {
  display: flex;
  gap: 1.5rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--brand-green);
  box-shadow: 0 0 8px var(--brand-green);
}

.status-dot.syncing {
  background: var(--brand-yellow);
  box-shadow: 0 0 8px var(--brand-yellow);
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.version-info {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  
  .tabs-container {
    flex-wrap: wrap;
  }
  
  .tab-button {
    min-width: 150px;
  }
}

@media (max-width: 768px) {
  .dashboard-header,
  .dashboard-main,
  .dashboard-footer {
    padding: 1rem;
  }
  
  .tabs-container {
    flex-direction: column;
  }
  
  .tab-button {
    width: 100%;
    justify-content: flex-start;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .status-indicators {
    flex-wrap: wrap;
    justify-content: center;
  }
}
</style>
