<template>
  <div class="cli-terminal">
    <div class="terminal-header">
      <span class="prompt">~/skills/view</span>
      <span class="cursor">$</span>
      <a href="/" class="back-link">$cd ..</a>
    </div>

    <div v-if="loading" class="loading">
      <span class="comment">// loading...</span>
    </div>

    <div v-else-if="skill" class="skill-detail">
      <!-- 技能头部 -->
      <div class="skill-header">
        <div class="skill-path">
          <span class="keyword">const</span>
          <span class="name">{{ skill.name }}</span>
          <span class="punctuation">=</span>
          <span class="keyword">require</span>
          <span class="string">"{{ skill.directory }}"</span>
          <span class="punctuation">;</span>
        </div>
      </div>

      <!-- 描述 -->
      <div v-if="skill.description" class="skill-description">
        <span class="comment">// {{ skill.description }}</span>
      </div>

      <!-- 元数据 -->
      <div class="skill-meta">
        <div class="meta-item">
          <span class="keyword">import</span>
          <span class="name">{{ skill.repository?.full_name || 'Unknown' }}</span>
        </div>
        <div class="meta-item" v-if="skill.readme_url">
          <a :href="skill.readme_url" target="_blank" class="link">
            <span class="keyword">$open</span>
            <span class="string">README</span>
          </a>
        </div>
      </div>

      <!-- 分类标签 -->
      <div v-if="skill.categories && skill.categories.length > 0" class="skill-categories">
        <span class="keyword">export</span>
        <span class="punctuation">[</span>
        <span
          v-for="(cat, index) in skill.categories"
          :key="cat.id"
        >
          <span class="string">{{ cat.name }}</span>
          <span v-if="index < skill.categories.length - 1" class="punctuation">, </span>
        </span>
        <span class="punctuation">];</span>
      </div>

      <!-- 内容区域（可扩展） -->
      <div class="skill-content">
        <div class="content-header">
          <span class="prompt">$cat SKILL.md</span>
        </div>
        <div class="content-body">
          <span class="comment">// 技能内容展示区域</span>
          <span class="comment">// 可以在这里显示 SKILL.md 的完整内容</span>
        </div>
      </div>
    </div>

    <div v-else class="not-found">
      <span class="keyword">throw</span>
      <span class="keyword">new</span>
      <span class="name">Error</span>
      <span class="punctuation">(</span>
      <span class="string">"Skill not found"</span>
      <span class="punctuation">);</span>
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
  gap: 1rem;
}

.back-link {
  color: #7aa2f7;
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

.keyword {
  color: #bb9af7;
}

.name {
  color: #7dcfff;
}

.string {
  color: #9ece6a;
}

.punctuation {
  color: #9aa5ce;
}

.comment {
  color: #565f89;
}

.link {
  color: #7aa2f7;
}

.skill-header {
  margin-bottom: 1rem;
}

.skill-path {
  padding-left: 1rem;
}

.skill-description {
  margin-bottom: 1rem;
  padding-left: 1rem;
}

.skill-meta {
  padding-left: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  margin-bottom: 0.5rem;
}

.skill-categories {
  padding-left: 1rem;
  margin-bottom: 2rem;
}

.skill-content {
  margin-top: 2rem;
}

.content-header {
  margin-bottom: 1rem;
}

.content-body {
  padding-left: 1rem;
}

.loading {
  padding: 1rem;
}

.not-found {
  padding: 1rem;
}
</style>
