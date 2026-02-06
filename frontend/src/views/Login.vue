<template>
  <div class="login-container">
    <div class="login-wrapper">
      <!-- 登录卡片 -->
      <div class="login-card">
        <div class="card-header">
          <div class="logo-section">
            <div class="logo-icon">{ }</div>
            <h1 class="app-title">技能中心</h1>
          </div>
          <p class="welcome-text">欢迎回到您的技能管理平台</p>
        </div>

        <form @submit.prevent="handleLogin" class="login-form">
          <div v-if="error" class="error-banner">
            <span class="error-icon">⚠️</span>
            <span class="error-message">{{ error }}</span>
          </div>

          <div class="input-group">
            <label class="input-label" for="username">用户名</label>
            <div class="input-wrapper">
              <span class="input-prefix">@</span>
              <input
                id="username"
                v-model="username"
                type="text"
                placeholder="请输入用户名"
                :disabled="loading"
                @keyup.enter="$event.target.nextElementSibling?.focus()"
                class="form-input"
              />
            </div>
          </div>

          <div class="input-group">
            <label class="input-label" for="password">密码</label>
            <div class="input-wrapper">
              <span class="input-prefix">🔒</span>
              <input
                id="password"
                v-model="password"
                type="password"
                placeholder="请输入密码"
                :disabled="loading"
                @keyup.enter="handleLogin"
                class="form-input"
              />
            </div>
          </div>

          <button 
            type="submit" 
            class="login-button" 
            :disabled="loading || !username || !password"
          >
            <span v-if="loading" class="button-spinner"></span>
            <span v-else class="button-text">登录</span>
          </button>
        </form>

        <div class="login-footer">
          <div class="credentials-hint">
            <p class="hint-title">默认账户信息</p>
            <div class="credential-item">
              <span class="credential-label">用户名:</span>
              <span class="credential-value">admin</span>
            </div>
            <div class="credential-item">
              <span class="credential-label">密码:</span>
              <span class="credential-value">Admin@123</span>
            </div>
          </div>
          
          <div class="divider">
            <span>或者</span>
          </div>
          
          <button class="guest-button" @click="$router.push('/')">
            游客访问
          </button>
        </div>
      </div>

      <!-- 装饰元素 -->
      <div class="decorative-elements">
        <div class="floating-shape shape-1"></div>
        <div class="floating-shape shape-2"></div>
        <div class="floating-shape shape-3"></div>
      </div>
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
    error.value = 'Please enter both username and password'
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
    error.value = e.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

.login-wrapper {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 450px;
}

.login-card {
  background: rgba(26, 27, 38, 0.85);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 2.5rem;
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-lg);
  transition: transform var(--transition-normal);
}

.login-card:hover {
  transform: translateY(-5px);
}

.card-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logo-icon {
  font-size: 2.5rem;
  font-weight: bold;
  color: var(--brand-blue);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.app-title {
  font-size: 2rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.welcome-text {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-top: 0.5rem;
}

.login-form {
  margin-bottom: 2rem;
}

.error-banner {
  background: rgba(247, 118, 142, 0.15);
  border: 1px solid rgba(247, 118, 142, 0.3);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.error-icon {
  font-size: 1.2rem;
}

.error-message {
  color: var(--brand-red);
  font-weight: 500;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-label {
  display: block;
  color: var(--text-secondary);
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-prefix {
  position: absolute;
  left: 1rem;
  color: var(--text-tertiary);
  z-index: 2;
  font-size: 1.1rem;
}

.form-input {
  width: 100%;
  background: rgba(37, 38, 55, 0.6);
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  padding: 1rem 1rem 1rem 3rem;
  border-radius: 10px;
  font-family: inherit;
  font-size: 1rem;
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--brand-blue);
  box-shadow: 0 0 0 3px rgba(122, 162, 247, 0.2);
}

.form-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-input::placeholder {
  color: var(--text-tertiary);
}

.login-button {
  width: 100%;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  color: white;
  border: none;
  padding: 1.1rem;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-normal);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.button-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.login-footer {
  text-align: center;
}

.credentials-hint {
  background: rgba(187, 154, 247, 0.1);
  border: 1px solid rgba(187, 154, 247, 0.2);
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.hint-title {
  color: var(--brand-purple);
  font-weight: 600;
  margin-bottom: 0.75rem;
  font-size: 0.95rem;
}

.credential-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
}

.credential-item:last-child {
  margin-bottom: 0;
}

.credential-label {
  color: var(--text-secondary);
}

.credential-value {
  color: var(--brand-purple);
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.divider {
  position: relative;
  margin: 1.5rem 0;
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-color);
  z-index: 1;
}

.divider span {
  background: rgba(26, 27, 38, 0.85);
  padding: 0 1rem;
  position: relative;
  z-index: 2;
}

.guest-button {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all var(--transition-fast);
  width: 100%;
}

.guest-button:hover {
  border-color: var(--brand-blue);
  color: var(--brand-blue);
  background: rgba(122, 162, 247, 0.1);
}

/* 装饰元素 */
.decorative-elements {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 1;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  opacity: 0.1;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 150px;
  height: 150px;
  top: 10%;
  left: 5%;
  animation-delay: 0s;
}

.shape-2 {
  width: 100px;
  height: 100px;
  top: 60%;
  right: 10%;
  animation-delay: 2s;
}

.shape-3 {
  width: 80px;
  height: 80px;
  bottom: 20%;
  left: 15%;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0) rotate(0deg); }
  25% { transform: translate(20px, -20px) rotate(90deg); }
  50% { transform: translate(-10px, -40px) rotate(180deg); }
  75% { transform: translate(-30px, -10px) rotate(270deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .login-container {
    padding: 1rem;
  }
  
  .login-card {
    padding: 2rem 1.5rem;
  }
  
  .app-title {
    font-size: 1.75rem;
  }
  
  .floating-shape {
    display: none;
  }
}
</style>
