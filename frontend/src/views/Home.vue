<template>
  <div class="cli-terminal">
    <!-- 顶部导航栏 -->
    <div class="terminal-header">
      <span class="prompt">~/skills</span>
      <span class="cursor">$</span>
      <span class="nav-items">
        <a href="/categories">$cd categories</a>
        <span class="nav-separator">;</span>
        <a href="/admin">$cd admin</a>
      </span>
    </div>

    <!-- 欢迎信息 -->
    <div class="terminal-content">
      <div class="system-info">
        <span class="comment">## export</span>
      </div>
      <div class="info-block">
        <span class="keyword">const</span>
        <span class="name">platform</span>
        <span class="operator">=</span>
        <span class="string">"Skills Platform"</span>
        <span class="punctuation">;</span>
      </div>
      <div class="info-block">
        <span class="keyword">import</span>
        <span class="name">内部技能管理平台</span>
        <span class="keyword">from</span>
        <span class="string">"@company/internal"</span>
        <span class="punctuation">;</span>
      </div>

      <div class="system-info">
        <span class="comment">// system.info</span>
      </div>
      <div class="info-block">
        <span class="bracket">[</span>
        <span class="string">"INFO"</span>
        <span class="bracket">]</span>
      </div>
      <div class="info-block">
        <span class="name">platform</span>
        <span class="punctuation">.</span>
        <span class="function">description</span>
        <span class="punctuation">=</span>
        <span class="string">"发现和管理内部技能"</span>
        <span class="punctuation">;</span>
      </div>

      <!-- 快速导航 -->
      <div class="quick-nav">
        <div class="nav-section">
          <span class="prompt">$cd</span>
          <a href="/categories">categories</a>
          <span class="comment">// 按分类浏览技能</span>
        </div>
        <div class="nav-section">
          <span class="prompt">$cd</span>
          <a href="/admin">admin</a>
          <span class="comment">// 管理面板（需登录）</span>
        </div>
      </div>
    </div>

    <!-- 示例分类展示 -->
    <div class="categories-preview" v-if="categories.length > 0">
      <div class="section-header">
        <span class="prompt">$ls categories/</span>
      </div>
      <div class="category-list">
        <div
          v-for="cat in categories.slice(0, 6)"
          :key="cat.id"
          class="category-item"
          @click="$router.push(`/categories?slug=${cat.slug}`)"
        >
          <span class="filename">{{ cat.slug }}.ts</span>
          <span class="keyword">export</span>
          <span class="name">{{ cat.name }}</span>
          <span class="comment">// {{ cat.skill_count || 0 }} 个技能</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../api'

const categories = ref<any[]>([])

onMounted(async () => {
  try {
    const data = await api.get('/categories')
    categories.value = data
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
})
</script>

<style scoped>
.cli-terminal {
  min-height: 100vh;
  padding: 2rem;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-header {
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
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

.nav-items {
  margin-left: 2rem;
  display: flex;
  gap: 1rem;
}

.nav-items a {
  color: #7aa2f7;
}

.nav-separator {
  color: #565f89;
}

.terminal-content {
  margin-bottom: 2rem;
}

.system-info {
  margin-bottom: 0.5rem;
}

.info-block {
  padding-left: 1rem;
  margin-bottom: 0.5rem;
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

.string {
  color: #9ece6a;
}

.operator {
  color: #bb9af7;
}

.punctuation {
  color: #9aa5ce;
}

.bracket {
  color: #9aa5ce;
}

.function {
  color: #7aa2f7;
}

.quick-nav {
  margin-top: 1rem;
  padding-left: 1rem;
}

.nav-section {
  margin-bottom: 0.5rem;
}

.nav-section a {
  color: #7dcfff;
}

.categories-preview {
  margin-top: 2rem;
}

.section-header {
  margin-bottom: 1rem;
}

.category-list {
  padding-left: 1rem;
}

.category-item {
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.category-item:hover .name {
  text-decoration: underline;
}

.filename {
  color: #7aa2f7;
  margin-right: 0.5rem;
}
</style>
