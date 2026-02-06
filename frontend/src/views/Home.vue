<template>
  <div class="home-container">
    <!-- 头部区域 -->
    <header class="hero-section">
      <div class="hero-content">
        <div class="logo-area">
          <div class="logo-symbol">{ }</div>
          <h1 class="platform-title">技能中心</h1>
        </div>
        <p class="platform-subtitle">发现 • 组织 • 分享内部技能</p>
        
        <div class="navigation-grid">
          <div class="nav-card" @click="$router.push('/categories')">
            <div class="card-icon">
              <span class="icon-symbol">📂</span>
            </div>
            <h3>按分类浏览</h3>
            <p>探索按功能领域和专业领域组织的技能</p>
          </div>

          <div class="nav-card" @click="$router.push('/admin')">
            <div class="card-icon">
              <span class="icon-symbol">⚙️</span>
            </div>
            <h3>管理系统</h3>
            <p>管理仓库、分类和用户访问权限（需要登录）</p>
          </div>
        </div>
      </div>
    </header>

    <!-- 统计信息区域 -->
    <section class="stats-section" v-if="stats.total_skills > 0">
      <div class="stats-container">
        <div class="stat-item">
          <div class="stat-number">{{ stats.total_skills }}</div>
          <div class="stat-label">总技能数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.total_categories }}</div>
          <div class="stat-label">分类数</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">{{ stats.total_repositories }}</div>
          <div class="stat-label">仓库数</div>
        </div>
      </div>
    </section>

    <!-- 热门分类展示 -->
    <section class="categories-section" v-if="categories.length > 0">
      <div class="section-header">
        <h2>热门分类</h2>
        <div class="section-divider"></div>
      </div>
      
      <div class="categories-grid">
        <div
          v-for="cat in categories.slice(0, 8)"
          :key="cat.id"
          class="category-card"
          @click="$router.push(`/categories?slug=${cat.slug}`)"
        >
          <div class="category-icon">
            <span>{{ cat.slug.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="category-content">
            <h3 class="category-name">{{ cat.name }}</h3>
            <p class="category-count">{{ cat.skill_count || 0 }} 个技能</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 底部CTA -->
    <footer class="cta-section">
      <div class="cta-content">
        <p>准备好发现精彩技能了吗？</p>
        <button class="cta-button" @click="$router.push('/categories')">
          探索分类
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'

const categories = ref<any[]>([])
const stats = ref({
  total_skills: 0,
  total_categories: 0,
  total_repositories: 0
})

onMounted(async () => {
  try {
    // 加载分类数据
    const categoryData = await api.get('/categories')
    categories.value = categoryData
    
    // 获取统计信息
    const [skillsRes, reposRes] = await Promise.all([
      api.get('/skills?page_size=1'),
      api.get('/repositories')
    ])
    
    stats.value = {
      total_skills: skillsRes.total || 0,
      total_categories: categoryData.length,
      total_repositories: Array.isArray(reposRes) ? reposRes.length : 0
    }
  } catch (e) {
    console.error('Failed to load data:', e)
  }
})
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
}

.hero-section {
  padding: 4rem 2rem;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(122, 162, 247, 0.15) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(187, 154, 247, 0.15) 0%, transparent 40%);
  pointer-events: none;
}

.hero-content {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.logo-area {
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.logo-symbol {
  font-size: 3rem;
  font-weight: bold;
  color: var(--brand-blue);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

.platform-title {
  font-size: 3.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.platform-subtitle {
  font-size: 1.25rem;
  color: var(--text-secondary);
  margin-bottom: 3rem;
  font-weight: 300;
}

.navigation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 3rem;
}

.nav-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 2rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  backdrop-filter: blur(10px);
}

.nav-card:hover {
  transform: translateY(-5px);
  border-color: var(--brand-blue);
  box-shadow: var(--shadow-lg);
}

.card-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.icon-symbol {
  font-size: 1.8rem;
}

.nav-card h3 {
  color: var(--text-primary);
  margin-bottom: 0.75rem;
  font-size: 1.25rem;
}

.nav-card p {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  line-height: 1.5;
}

.stats-section {
  padding: 3rem 2rem;
  background: rgba(21, 22, 34, 0.6);
  backdrop-filter: blur(10px);
}

.stats-container {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  text-align: center;
}

.stat-item {
  padding: 1.5rem;
  background: rgba(26, 27, 38, 0.5);
  border-radius: 10px;
  border: 1px solid var(--border-light);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--brand-blue);
  margin-bottom: 0.5rem;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 1rem;
}

.categories-section {
  padding: 4rem 2rem;
}

.section-header {
  text-align: center;
  margin-bottom: 3rem;
}

.section-header h2 {
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 1rem;
}

.section-divider {
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, var(--brand-blue), var(--brand-purple));
  margin: 0 auto;
  border-radius: 2px;
}

.categories-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.category-card {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 10px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all var(--transition-normal);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  gap: 1rem;
}

.category-card:hover {
  transform: translateY(-3px);
  border-color: var(--brand-blue);
  box-shadow: var(--shadow-md);
}

.category-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  color: white;
  font-size: 1.2rem;
}

.category-content {
  flex: 1;
}

.category-name {
  color: var(--text-primary);
  margin-bottom: 0.25rem;
  font-size: 1.1rem;
}

.category-count {
  color: var(--text-tertiary);
  font-size: 0.9rem;
}

.cta-section {
  padding: 4rem 2rem;
  text-align: center;
  background: rgba(21, 22, 34, 0.8);
  backdrop-filter: blur(10px);
}

.cta-content p {
  font-size: 1.25rem;
  color: var(--text-secondary);
  margin-bottom: 2rem;
}

.cta-button {
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
  color: white;
  border: none;
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-normal);
  font-weight: 500;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .platform-title {
    font-size: 2.5rem;
  }
  
  .navigation-grid {
    grid-template-columns: 1fr;
  }
  
  .categories-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-container {
    grid-template-columns: 1fr;
  }
}
</style>
