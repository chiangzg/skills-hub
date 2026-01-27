<template>
  <div class="admin-panel">
    <div class="admin-header">
      <span class="prompt">~/skills/admin</span>
      <span class="cursor">$</span>
      <a href="/" class="back-link">$cd ..</a>
      <span class="user-info">
        <span class="comment">// {{ username }}</span>
      </span>
      <button @click="logout" class="logout-btn">
        <span class="keyword">$exit</span>
      </button>
    </div>

    <!-- 标签页导航 -->
    <div class="tabs">
      <button
        :class="['tab', { active: activeTab === 'repositories' }]"
        @click="activeTab = 'repositories'"
      >
        <span class="keyword">$ls</span>
        <span class="name">repositories</span>
      </button>
      <button
        :class="['tab', { active: activeTab === 'categories' }]"
        @click="activeTab = 'categories'"
      >
        <span class="keyword">$ls</span>
        <span class="name">categories</span>
      </button>
      <button
        v-if="isAdmin"
        :class="['tab', { active: activeTab === 'users' }]"
        @click="activeTab = 'users'"
      >
        <span class="keyword">$ls</span>
        <span class="name">users</span>
      </button>
    </div>

    <!-- 仓库管理 -->
    <div v-show="activeTab === 'repositories'" class="tab-content">
      <RepositoryPanel />
    </div>

    <!-- 分类管理 -->
    <div v-show="activeTab === 'categories'" class="tab-content">
      <CategoryPanel />
    </div>

    <!-- 用户管理 -->
    <div v-show="activeTab === 'users'" class="tab-content">
      <UserPanel v-if="isAdmin" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import RepositoryPanel from '../../components/admin/RepositoryPanel.vue'
import CategoryPanel from '../../components/admin/CategoryPanel.vue'
import UserPanel from '../../components/admin/UserPanel.vue'

const router = useRouter()
const activeTab = ref('repositories')
const username = ref(localStorage.getItem('username') || '')
const isAdmin = ref(localStorage.getItem('userRole') === 'admin')

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userRole')
  localStorage.removeItem('username')
  router.push('/login')
}
</script>

<style scoped>
.admin-panel {
  min-height: 100vh;
  padding: 2rem;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.admin-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
}

.prompt {
  color: #9aa5ce;
}

.cursor {
  color: #9aa5ce;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.back-link {
  color: #7aa2f7;
}

.user-info {
  margin-left: auto;
}

.comment {
  color: #565f89;
}

.logout-btn {
  background: transparent;
  border: none;
  color: #f7768e;
  cursor: pointer;
  font-family: inherit;
}

.keyword {
  color: #bb9af7;
}

.name {
  color: #7dcfff;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.tab {
  background: transparent;
  border: none;
  color: #565f89;
  cursor: pointer;
  padding: 0.5rem 1rem;
  font-family: inherit;
  transition: color 0.2s;
}

.tab:hover {
  color: #7aa2f7;
}

.tab.active {
  color: #7aa2f7;
  border-bottom: 1px solid #7aa2f7;
}

.tab-content {
  padding: 1rem;
}
</style>
