<template>
  <div class="skill-detail-container">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <div class="breadcrumb-navigation">
          <button class="back-button" @click="$router.go(-1)">
            ← 返回
          </button>
          <div class="breadcrumb-separator">/</div>
          <span class="current-page">技能详情</span>
        </div>
        <div v-if="loading" class="loading-placeholder">
          <div class="skeleton-title"></div>
        </div>
      </div>
    </header>

    <div class="main-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>正在加载技能详情...</p>
      </div>

      <div v-else-if="skill" class="skill-layout">
        <!-- 左侧主要内容 -->
        <div class="skill-main">
          <!-- 技能头部信息 -->
          <div class="skill-header-card">
            <div class="skill-title-section">
              <h1 class="skill-title">{{ skill.name }}</h1>
              <div class="skill-tags">
                <span 
                  v-for="tag in skill.tags" 
                  :key="tag"
                  class="tag"
                >
                  #{{ tag }}
                </span>
              </div>
            </div>
            
            <p v-if="skill.description" class="skill-description">
              {{ skill.description }}
            </p>

            <div class="skill-metadata">
              <div class="meta-item">
                <span class="meta-label">仓库</span>
                <span class="meta-value">{{ skill.repository?.full_name || '未知' }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">路径</span>
                <span class="meta-value path-value">{{ skill.directory }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">最后更新</span>
                <span class="meta-value">{{ formatDate(skill.updated_at) }}</span>
              </div>
            </div>
          </div>

          <!-- 分类信息 -->
          <div v-if="skill.categories && skill.categories.length > 0" class="categories-card">
            <h2 class="section-title">所属分类</h2>
            <div class="categories-list">
              <div
                v-for="cat in skill.categories"
                :key="cat.id"
                class="category-chip"
                @click="$router.push(`/categories?slug=${cat.slug}`)"
              >
                {{ cat.name }}
              </div>
            </div>
          </div>

          <!-- README内容区域 -->
          <div class="readme-card">
            <div class="card-header">
              <h2 class="section-title">文档说明</h2>
              <a 
                v-if="skill.readme_url" 
                :href="skill.readme_url" 
                target="_blank" 
                class="external-link"
              >
                查看原文 →
              </a>
            </div>
            
            <div class="readme-content">
              <div v-if="skill.content" class="markdown-content" v-html="renderMarkdown(skill.content)"></div>
              <div v-else class="empty-readme">
                <div class="empty-icon">📄</div>
                <p>该技能暂无文档内容。</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧侧边栏 -->
        <aside class="skill-sidebar">
          <!-- 操作按钮 -->
          <div class="actions-card">
            <h3 class="card-title">操作</h3>
            <div class="action-buttons">
              <button 
                v-if="skill.readme_url"
                :href="skill.readme_url" 
                target="_blank" 
                class="action-button primary"
              >
                <span class="button-icon">📖</span>
                查看文档
              </button>
              <button class="action-button secondary">
                <span class="button-icon">⭐</span>
                收藏
              </button>
              <button class="action-button secondary">
                <span class="button-icon">📤</span>
                分享
              </button>
            </div>
          </div>

          <!-- 技术栈 -->
          <div v-if="skill.technologies && skill.technologies.length > 0" class="tech-card">
            <h3 class="card-title">技术栈</h3>
            <div class="tech-tags">
              <span 
                v-for="tech in skill.technologies" 
                :key="tech"
                class="tech-tag"
              >
                {{ tech }}
              </span>
            </div>
          </div>

          <!-- 相关技能 -->
          <div class="related-card">
            <h3 class="card-title">相关技能</h3>
            <div class="related-list">
              <div class="related-item skeleton" v-for="i in 3" :key="i"></div>
            </div>
          </div>
        </aside>
      </div>

      <div v-else class="not-found-state">
        <div class="error-icon">⚠️</div>
        <h2>未找到技能</h2>
        <p>找不到请求的技能信息。</p>
        <button class="back-home-button" @click="$router.push('/')">
          返回首页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const skill = ref<any>(null)
const loading = ref(true)

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    skill.value = await api.get(`/skills/${id}`)
  } catch (e) {
    console.error('Failed to load skill:', e)
  }
  loading.value = false
})

function formatDate(dateString: string) {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function renderMarkdown(content: string) {
  // 简单的markdown渲染（实际项目中可以使用markdown-it等库）
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.skill-detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.page-header {
  padding: 1.5rem 2rem;
  background: rgba(21, 22, 34, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-light);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.breadcrumb-navigation {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.back-button {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-size: 0.9rem;
}

.back-button:hover {
  border-color: var(--brand-blue);
  color: var(--brand-blue);
}

.breadcrumb-separator {
  color: var(--text-tertiary);
}

.current-page {
  color: var(--brand-blue);
  font-weight: 500;
}

.loading-placeholder .skeleton-title {
  width: 300px;
  height: 2rem;
  background: linear-gradient(90deg, var(--border-color) 25%, transparent 50%, var(--border-color) 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 4px;
}

@keyframes loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

.loading-state {
  text-align: center;
  padding: 4rem;
  color: var(--text-secondary);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-color);
  border-top: 3px solid var(--brand-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.skill-layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 2rem;
}

/* 主要内容区域 */
.skill-main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.skill-header-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.skill-title-section {
  margin-bottom: 1.5rem;
}

.skill-title {
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-weight: 700;
}

.skill-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tag {
  background: rgba(187, 154, 247, 0.2);
  color: var(--brand-purple);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.skill-description {
  color: var(--text-secondary);
  font-size: 1.1rem;
  line-height: 1.7;
  margin-bottom: 2rem;
  padding-left: 1rem;
  border-left: 3px solid var(--brand-blue);
}

.skill-metadata {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.meta-label {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.meta-value {
  color: var(--text-primary);
  font-weight: 500;
}

.path-value {
  font-family: 'JetBrains Mono', monospace;
  background: rgba(37, 38, 55, 0.5);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.categories-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
}

.section-title {
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-size: 1.25rem;
  font-weight: 600;
}

.categories-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.category-chip {
  background: rgba(122, 162, 247, 0.2);
  color: var(--brand-blue);
  padding: 0.5rem 1rem;
  border-radius: 25px;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-weight: 500;
}

.category-chip:hover {
  background: rgba(122, 162, 247, 0.3);
  transform: translateY(-2px);
}

.readme-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.external-link {
  color: var(--brand-blue);
  text-decoration: none;
  font-weight: 500;
  transition: color var(--transition-fast);
}

.external-link:hover {
  color: var(--brand-cyan);
  text-decoration: underline;
}

.readme-content {
  min-height: 300px;
}

.markdown-content {
  color: var(--text-secondary);
  line-height: 1.7;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3 {
  color: var(--text-primary);
  margin: 1.5rem 0 1rem 0;
}

.markdown-content code {
  background: rgba(37, 38, 55, 0.8);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
}

.empty-readme {
  text-align: center;
  padding: 3rem;
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

/* 侧边栏 */
.skill-sidebar {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.actions-card,
.tech-card,
.related-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
}

.card-title {
  color: var(--text-primary);
  margin-bottom: 1rem;
  font-size: 1.1rem;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-weight: 500;
  border: none;
  width: 100%;
  text-align: left;
}

.action-button.primary {
  background: var(--brand-blue);
  color: white;
}

.action-button.primary:hover {
  background: var(--brand-cyan);
  transform: translateY(-2px);
}

.action-button.secondary {
  background: rgba(37, 38, 55, 0.6);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.action-button.secondary:hover {
  background: rgba(122, 162, 247, 0.1);
  border-color: var(--brand-blue);
  color: var(--brand-blue);
}

.button-icon {
  font-size: 1.2rem;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tech-tag {
  background: rgba(187, 154, 247, 0.15);
  color: var(--brand-purple);
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.85rem;
}

.related-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.related-item.skeleton {
  height: 60px;
  background: linear-gradient(90deg, var(--border-color) 25%, transparent 50%, var(--border-color) 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 8px;
}

.not-found-state {
  text-align: center;
  padding: 4rem;
  color: var(--text-secondary);
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.not-found-state h2 {
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.back-home-button {
  background: var(--brand-blue);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all var(--transition-fast);
  margin-top: 1rem;
}

.back-home-button:hover {
  background: var(--brand-cyan);
  transform: translateY(-2px);
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .skill-layout {
    grid-template-columns: 1fr;
  }
  
  .skill-sidebar {
    order: 1;
  }
  
  .skill-main {
    order: 2;
  }
}

@media (max-width: 768px) {
  .skill-title {
    font-size: 1.5rem;
  }
  
  .skill-metadata {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: row;
    flex-wrap: wrap;
  }
  
  .action-button {
    flex: 1;
    min-width: 120px;
  }
}
</style>
