<template>
  <div class="login-container cli-terminal">
    <div class="terminal-header">
      <span class="prompt">~/skills/login</span>
      <span class="cursor">$</span>
    </div>

    <form @submit.prevent="handleLogin" class="login-form">
      <div v-if="error" class="error-message">
        <span class="comment">// Error: {{ error }}</span>
      </div>

      <div class="input-line">
        <span class="prompt">$ username:</span>
        <input
          v-model="username"
          type="text"
          placeholder="admin"
          @keyup.enter="$event.target.nextElementSibling?.focus()"
        />
      </div>

      <div class="input-line">
        <span class="prompt">$ password:</span>
        <input
          v-model="password"
          type="password"
          placeholder="•••••••"
          @keyup.enter="handleLogin"
        />
      </div>

      <button type="submit" class="terminal-btn" :disabled="loading">
        <span class="prompt">$</span>
        <span class="keyword">exec</span>
        <span class="name">login</span>
      </button>
    </form>

    <div class="hint">
      <span class="comment">// 默认账号: admin / Admin@123</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi, api } from '../api'

const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const response: any = await authApi.login(username.value, password.value)

    // 保存 token 和用户信息
    api.setToken(response.access_token)
    localStorage.setItem('userRole', response.user.role)
    localStorage.setItem('username', response.user.username)

    // 跳转到原来的页面或首页
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  } catch (e: any) {
    error.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-header {
  margin-bottom: 3rem;
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

.login-form {
  width: 100%;
  max-width: 400px;
}

.error-message {
  margin-bottom: 1rem;
  padding: 0.5rem;
}

.input-line {
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
}

.input-line input {
  flex: 1;
  background: #1a1b26;
  border: 1px solid #414868;
  color: #c0caf5;
  padding: 0.5rem 1rem;
  font-family: inherit;
  font-size: 1rem;
  outline: none;
}

.input-line input:focus {
  border-color: #7aa2f7;
}

.terminal-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: #1a1b26;
  border: 1px solid #7aa2f7;
  color: #7aa2f7;
  cursor: pointer;
  font-family: inherit;
  font-size: 1rem;
  transition: all 0.2s;
}

.terminal-btn:hover:not(:disabled) {
  background: #7aa2f7;
  color: #1a1b26;
}

.terminal-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.comment {
  color: #565f89;
}

.keyword {
  color: #bb9af7;
}

.name {
  color: #7dcfff;
}

.hint {
  margin-top: 2rem;
}
</style>
