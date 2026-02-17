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
                v-if="skill.raw_content_url" 
                :href="skill.raw_content_url" 
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
                @click="openReadme"
                class="action-button primary"
              >
                <span class="button-icon">📖</span>
                查看仓库
              </button>
              <button
                v-if="skill.cli_command"
                @click="copyCliCommand"
                class="action-button download"
              >
                <span class="button-icon">📋</span>
                {{ copyButtonText }}
              </button>
              <button
                @click="shareSkill"
                class="action-button secondary"
                :class="{ 'copied': shareButtonText !== '分享' }"
              >
                <span class="button-icon">📤</span>
                {{ shareButtonText }}
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
            <div v-if="loadingRelated" class="related-list">
              <div class="related-item skeleton" v-for="i in 3" :key="i"></div>
            </div>
            <div v-else-if="relatedSkills.length > 0" class="related-list">
              <div
                v-for="relatedSkill in relatedSkills"
                :key="relatedSkill.id"
                class="related-item"
                @click="goToSkill(relatedSkill.id)"
              >
                <div class="related-skill-name">{{ relatedSkill.name }}</div>
                <div class="related-skill-meta">
                  <span v-if="relatedSkill.stars > 0" class="related-stars">⭐ {{ relatedSkill.stars }}</span>
                  <span class="related-desc" v-if="relatedSkill.description">
                    {{ relatedSkill.description.slice(0, 30) }}{{ relatedSkill.description.length > 30 ? '...' : '' }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="related-empty">
              暂无相关技能
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
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import type { Skill } from '../types/api'

const route = useRoute()
const router = useRouter()
const skill = ref<Skill | null>(null)
const loading = ref(true)
const copyButtonText = ref('复制安装命令')
const relatedSkills = ref<Skill[]>([])
const loadingRelated = ref(false)
const shareButtonText = ref('分享')

onMounted(async () => {
  const id = Number(route.params.id)
  try {
    skill.value = await api.get(`/skills/${id}`)
    // 获取相关技能
    await loadRelatedSkills()
  } catch (e) {
    console.error('Failed to load skill:', e)
  }
  loading.value = false
})

// 当路由参数变化时重新加载
watch(() => route.params.id, async (newId) => {
  if (newId) {
    loading.value = true
    try {
      skill.value = await api.get(`/skills/${Number(newId)}`)
      await loadRelatedSkills()
    } catch (e) {
      console.error('Failed to load skill:', e)
    }
    loading.value = false
  }
})

async function loadRelatedSkills() {
  if (!skill.value || !skill.value.categories || skill.value.categories.length === 0) {
    relatedSkills.value = []
    return
  }

  loadingRelated.value = true
  try {
    // 获取第一个分类的其他技能
    const categoryId = skill.value.categories[0].id
    const response = await api.get<{items: Skill[], total: number}>(`/skills?category_id=${categoryId}&sort_by=stars&sort_order=desc&page_size=10`)
    // 过滤掉当前技能，并限制显示数量
    relatedSkills.value = response.items
      .filter(s => s.id !== skill.value?.id)
      .slice(0, 5)
  } catch (e) {
    console.error('Failed to load related skills:', e)
    relatedSkills.value = []
  }
  loadingRelated.value = false
}

function formatDate(dateString: string) {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

function renderMarkdown(content: string) {
  // 使用 marked 将 markdown 转换为 HTML
  const rawHtml = marked(content)

  // 使用 DOMPurify 清理 HTML，防止 XSS 攻击
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'hr', 'table', 'thead', 'tbody', 'tr', 'th', 'td'],
    ALLOWED_ATTR: ['href', 'title', 'class']
  })
}

function openReadme() {
  if (skill.value?.readme_url) {
    window.open(skill.value.readme_url, '_blank')
  }
}

async function copyCliCommand() {
  if (!skill.value?.cli_command) return
  
  try {
    await navigator.clipboard.writeText(skill.value.cli_command)
    copyButtonText.value = '已复制！'
    setTimeout(() => {
      copyButtonText.value = '复制安装命令'
    }, 2000)
  } catch (err) {
    console.error('Failed to copy:', err)
    // 降级方案：使用传统复制方法
    const textArea = document.createElement('textarea')
    textArea.value = skill.value.cli_command
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    copyButtonText.value = '已复制！'
    setTimeout(() => {
      copyButtonText.value = '复制安装命令'
    }, 2000)
  }
}

async function shareSkill() {
  const url = window.location.href
  
  try {
    await navigator.clipboard.writeText(url)
    shareButtonText.value = '链接已复制！'
    setTimeout(() => {
      shareButtonText.value = '分享'
    }, 2500)
  } catch (err) {
    console.error('Failed to copy:', err)
    // 降级方案：使用传统复制方法
    const textArea = document.createElement('textarea')
    textArea.value = url
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
    shareButtonText.value = '链接已复制！'
    setTimeout(() => {
      shareButtonText.value = '分享'
    }, 2500)
  }
}

function goToSkill(skillId: number) {
  router.push(`/skills/${skillId}`)
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

.action-button.download {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
}

.action-button.download:hover {
  background: linear-gradient(135deg, #34d399 0%, #10b981 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.action-button.secondary.copied {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10b981;
  color: #10b981;
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

.related-item {
  padding: 0.75rem;
  background: rgba(37, 38, 55, 0.5);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.related-item:hover {
  background: rgba(122, 162, 247, 0.1);
  border-color: var(--brand-blue);
  transform: translateX(4px);
}

.related-item.skeleton {
  height: 60px;
  background: linear-gradient(90deg, var(--border-color) 25%, transparent 50%, var(--border-color) 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 8px;
}

.related-skill-name {
  color: var(--text-primary);
  font-weight: 500;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
}

.related-skill-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.related-stars {
  color: #fbbf24;
  font-size: 0.8rem;
  font-weight: 500;
}

.related-desc {
  color: var(--text-tertiary);
  font-size: 0.8rem;
}

.related-empty {
  text-align: center;
  padding: 1.5rem;
  color: var(--text-tertiary);
  font-size: 0.9rem;
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
