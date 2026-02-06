<template>
  <div class="categories-container">
    <!-- 页面头部 -->
    <header class="page-header">
      <div class="header-content">
        <button class="back-button" @click="$router.push('/')">
          ← 返回首页
        </button>
        <h1 class="page-title">技能分类</h1>
        <p class="page-subtitle">按分类浏览和探索技能</p>
      </div>
    </header>

    <div class="main-content">
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>正在加载分类...</p>
      </div>

      <div v-else class="categories-layout">
        <!-- 分类树侧边栏 -->
        <aside class="categories-sidebar">
          <div class="sidebar-header">
            <h2>分类树</h2>
            <div class="category-stats">
              共 {{ totalCategories }} 个分类
            </div>
          </div>
          
          <div class="category-tree">
            <div 
              v-for="cat in categories" 
              :key="cat.id"
              class="category-node"
            >
              <div 
                class="category-item"
                :class="{ expanded: expandedCategories.has(cat.id), active: selectedCategory?.id === cat.id }"
                @click="toggleCategory(cat)"
              >
                <div class="category-toggle">
                  <span class="toggle-icon" v-if="cat.children && cat.children.length > 0">
                    {{ expandedCategories.has(cat.id) ? '▼' : '▶' }}
                  </span>
                  <span class="category-name">{{ cat.name }}</span>
                </div>
                <span class="skill-count">{{ cat.skill_count || 0 }}</span>
              </div>
              
              <!-- 子分类 -->
              <div v-if="cat.children && cat.children.length > 0 && expandedCategories.has(cat.id)" class="sub-categories">
                <div
                  v-for="child in cat.children"
                  :key="child.id"
                  class="sub-category-item"
                  :class="{ active: selectedCategory?.id === child.id }"
                  @click="viewCategory(child)"
                >
                  <span class="sub-category-name">{{ child.name }}</span>
                  <span class="skill-count">{{ child.skill_count || 0 }}</span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        <!-- 技能列表主区域 -->
        <main class="skills-main">
          <div v-if="selectedCategory" class="category-header">
            <div class="category-breadcrumb">
              <span class="breadcrumb-item">{{ selectedCategory.name }}</span>
              <span class="breadcrumb-separator">/</span>
              <span class="breadcrumb-count">{{ skills.length }} 个技能</span>
            </div>
          </div>

          <div class="skills-grid" v-if="skills.length > 0">
            <div
              v-for="skill in skills"
              :key="skill.id"
              class="skill-card"
              @click="viewSkill(skill)"
            >
              <div class="skill-header">
                <h3 class="skill-name">{{ skill.name }}</h3>
                <div class="skill-meta">
                  <span class="repository">{{ skill.repository?.full_name || '未知' }}</span>
                </div>
              </div>
              
              <p class="skill-description" v-if="skill.description">
                {{ skill.description }}
              </p>
              
              <div class="skill-footer">
                <div class="skill-path">
                  <span class="path-icon">📁</span>
                  <span class="path-text">{{ skill.directory }}</span>
                </div>
                <div class="skill-actions">
                  <button class="action-button view-button">
                    查看详情
                  </button>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <div class="empty-icon">📭</div>
            <h3>暂无技能</h3>
            <p>该分类下还没有任何技能。</p>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const categories = ref<any[]>([])
const skills = ref<any[]>([])
const selectedCategory = ref<any>(null)
const loading = ref(true)
const expandedCategories = ref(new Set<number>())

const totalCategories = computed(() => {
  let count = categories.value.length
  categories.value.forEach(cat => {
    if (cat.children) {
      count += cat.children.length
    }
  })
  return count
})

onMounted(async () => {
  await loadCategories()

  const slug = route.query.slug as string
  if (slug) {
    await findAndSelectCategory(slug)
  }

  loading.value = false
})

async function loadCategories() {
  try {
    const data = await api.get('/categories/tree')
    categories.value = data
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

async function findAndSelectCategory(slug: string) {
  for (const cat of categories.value) {
    if (cat.slug === slug) {
      selectedCategory.value = cat
      expandedCategories.value.add(cat.id)
      await loadSkills(cat.id)
      return
    }
    if (cat.children) {
      for (const child of cat.children) {
        if (child.slug === slug) {
          selectedCategory.value = child
          expandedCategories.value.add(cat.id)
          await loadSkills(child.id)
          return
        }
      }
    }
  }
}

async function loadSkills(categoryId: number) {
  try {
    const data = await api.get(`/skills?category_id=${categoryId}&page_size=100`)
    skills.value = data.items
  } catch (e) {
    console.error('Failed to load skills:', e)
  }
}

function toggleCategory(cat: any) {
  const isExpanded = expandedCategories.value.has(cat.id)

  if (isExpanded) {
    // 收起时只做收起操作
    expandedCategories.value.delete(cat.id)
  } else {
    // 展开时
    expandedCategories.value.add(cat.id)

    // 如果有子分类，自动选择第一个
    if (cat.children && cat.children.length > 0) {
      viewCategory(cat.children[0])
    } else {
      // 没有子分类，直接选择当前分类
      viewCategory(cat)
    }
  }
}

function viewCategory(cat: any) {
  selectedCategory.value = cat
  loadSkills(cat.id)
}

function viewSkill(skill: any) {
  router.push(`/skills/${skill.id}`)
}
</script>

<style scoped>
.categories-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.page-header {
  padding: 2rem;
  background: rgba(21, 22, 34, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-light);
}

.header-content {
  max-width: 1400px;
  margin: 0 auto;
}

.back-button {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.back-button:hover {
  border-color: var(--brand-blue);
  color: var(--brand-blue);
}

.page-title {
  font-size: 2.5rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.page-subtitle {
  color: var(--text-tertiary);
  font-size: 1.1rem;
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

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.categories-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
}

/* 侧边栏样式 */
.categories-sidebar {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  height: fit-content;
}

.sidebar-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-light);
}

.sidebar-header h2 {
  color: var(--text-primary);
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
}

.category-stats {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.category-tree {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.category-node {
  margin-bottom: 0.25rem;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
  background: transparent;
}

.category-item:hover {
  background: rgba(122, 162, 247, 0.1);
}

.category-item.expanded {
  background: rgba(122, 162, 247, 0.15);
  border-left: 3px solid var(--brand-blue);
}

.category-item.active {
  background: rgba(122, 162, 247, 0.2);
  border-left: 3px solid var(--brand-blue);
}

.category-toggle {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.toggle-icon {
  color: var(--text-tertiary);
  font-size: 0.8rem;
  transition: transform var(--transition-fast);
}

.category-item.expanded .toggle-icon {
  transform: rotate(90deg);
}

.category-name {
  color: var(--text-primary);
  font-weight: 500;
}

.skill-count {
  background: rgba(122, 162, 247, 0.2);
  color: var(--brand-blue);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
}

.sub-categories {
  margin-left: 1.5rem;
  margin-top: 0.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sub-category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.sub-category-item:hover {
  background: rgba(122, 162, 247, 0.1);
}

.sub-category-item.active {
  background: rgba(122, 162, 247, 0.15);
}

.sub-category-name {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

/* 主内容区域 */
.skills-main {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 2rem;
  backdrop-filter: blur(10px);
}

.category-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-light);
}

.category-breadcrumb {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-secondary);
}

.breadcrumb-item {
  color: var(--brand-blue);
  font-weight: 500;
  font-size: 1.25rem;
}

.breadcrumb-separator {
  color: var(--text-tertiary);
}

.breadcrumb-count {
  background: rgba(122, 162, 247, 0.2);
  color: var(--brand-blue);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
}

.skills-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.skill-card {
  background: rgba(37, 38, 55, 0.6);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all var(--transition-normal);
}

.skill-card:hover {
  transform: translateY(-3px);
  border-color: var(--brand-blue);
  box-shadow: var(--shadow-md);
}

.skill-header {
  margin-bottom: 1rem;
}

.skill-name {
  color: var(--text-primary);
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.skill-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.repository {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  background: rgba(187, 154, 247, 0.15);
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
}

.skill-description {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  line-height: 1.6;
  font-size: 0.95rem;
}

.skill-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-path {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-tertiary);
  font-size: 0.85rem;
}

.path-icon {
  font-size: 1rem;
}

.action-button {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.view-button {
  background: var(--brand-blue);
  color: white;
  border: none;
}

.view-button:hover {
  background: var(--brand-cyan);
  transform: translateY(-1px);
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--text-secondary);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .categories-layout {
    grid-template-columns: 1fr;
  }
  
  .categories-sidebar {
    order: 2;
  }
  
  .skills-main {
    order: 1;
  }
}

@media (max-width: 768px) {
  .skills-grid {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 2rem;
  }
}
</style>
