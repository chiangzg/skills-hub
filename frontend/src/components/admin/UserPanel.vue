<template>
  <div class="user-panel">
    <div class="panel-header">
      <span class="prompt">$cat users.config</span>
      <button @click="showAddDialog = true" class="add-btn">
        <span class="keyword">$useradd</span>
      </button>
    </div>

    <!-- 用户列表 -->
    <div class="user-list">
      <div
        v-for="user in users"
        :key="user.id"
        class="user-item"
      >
        <div class="user-info">
          <span class="keyword">{{ user.role }}</span>
          <span class="name">{{ user.username }}</span>
          <span class="comment">// {{ user.email || 'no email' }}</span>
          <span class="status" :class="{ active: user.is_active, inactive: !user.is_active }">
            {{ user.is_active ? '✓' : '✗' }}
          </span>
        </div>
        <div class="user-actions">
          <button @click="resetPassword(user)" class="action-btn">
            <span class="keyword">$passwd</span>
          </button>
          <button v-if="user.username !== 'admin'" @click="deleteUser(user)" class="action-btn danger">
            <span class="keyword">$rm</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 添加用户对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay" @click.self="showAddDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span class="prompt">$useradd new</span>
        </div>
        <form @submit.prevent="addUser" class="dialog-form">
          <div class="form-row">
            <label class="label">
              <span class="keyword">username</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.username" class="input" placeholder="username" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">password</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.password" class="input" type="password" placeholder="•••••••" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">email</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.email" class="input" placeholder="email@example.com" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">role</span>
              <span class="punctuation">:</span>
            </label>
            <select v-model="form.role" class="input">
              <option value="maintainer">maintainer</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div class="dialog-actions">
            <button type="button" @click="showAddDialog = false" class="cancel-btn">
              <span class="keyword">$cancel</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="loading">
              <span class="keyword">$exec</span>
              <span class="name">create</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { userApi } from '../../api'

const users = ref<any[]>([])
const showAddDialog = ref(false)
const loading = ref(false)

const form = ref({
  username: '',
  password: '',
  email: '',
  role: 'maintainer'
})

onMounted(async () => {
  await loadUsers()
})

async function loadUsers() {
  try {
    users.value = await userApi.list()
  } catch (e) {
    console.error('Failed to load users:', e)
  }
}

async function addUser() {
  loading.value = true
  try {
    await userApi.create({
      username: form.value.username,
      password: form.value.password,
      email: form.value.email || undefined,
      role: form.value.role
    })
    showAddDialog.value = false
    form.value = { username: '', password: '', email: '', role: 'maintainer' }
    await loadUsers()
  } catch (e: any) {
    alert(e.message || '添加失败')
  } finally {
    loading.value = false
  }
}

async function resetPassword(user: any) {
  const newPassword = prompt(`重置用户 ${user.username} 的密码：`)
  if (!newPassword) return

  try {
    await userApi.resetPassword(user.id, newPassword)
    alert('密码已重置')
  } catch (e: any) {
    alert(e.message || '重置失败')
  }
}

async function deleteUser(user: any) {
  if (!confirm(`确定删除用户 ${user.username}？`)) return

  try {
    await userApi.delete(user.id)
    await loadUsers()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}
</script>

<style scoped>
.user-panel {
  padding: 1rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.prompt {
  color: #9aa5ce;
}

.keyword {
  color: #bb9af7;
}

.name {
  color: #7dcfff;
}

.punctuation {
  color: #9aa5ce;
}

.comment {
  color: #565f89;
}

.add-btn {
  background: transparent;
  border: 1px solid #7aa2f7;
  color: #7aa2f7;
  cursor: pointer;
  padding: 0.5rem 1rem;
  font-family: inherit;
}

.user-list {
  padding: 1rem 0;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #414868;
}

.user-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status {
  margin-left: 1rem;
}

.status.active {
  color: #9ece6a;
}

.status.inactive {
  color: #565f89;
}

.user-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  color: #7aa2f7;
  font-family: inherit;
}

.action-btn.danger {
  color: #f7768e;
}

/* 对话框 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: #1a1b26;
  border: 1px solid #414868;
  padding: 2rem;
  min-width: 400px;
}

.dialog-header {
  margin-bottom: 1.5rem;
}

.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.label {
  width: 100px;
}

.input {
  flex: 1;
  background: #16161e;
  border: 1px solid #414868;
  color: #c0caf5;
  padding: 0.5rem;
  font-family: inherit;
}

.input:focus {
  outline: none;
  border-color: #7aa2f7;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1rem;
}

.cancel-btn,
.submit-btn {
  padding: 0.5rem 1rem;
  font-family: inherit;
  cursor: pointer;
}

.cancel-btn {
  background: transparent;
  border: 1px solid #414868;
  color: #565f89;
}

.submit-btn {
  background: #7aa2f7;
  border: none;
  color: #1a1b26;
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
