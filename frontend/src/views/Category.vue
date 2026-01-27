<template>
  <div class="cli-terminal">
    <div class="terminal-header">
      <span class="prompt">~/skills/categories</span>
      <span class="cursor">$</span>
    </div>

    <div v-if="loading" class="loading">
      <span class="comment">// loading...</span>
    </div>

    <div v-else>
      <div class="category-tree" v-for="cat in categories" :key="cat.id">
        <div class="category-item" @click="toggleCategory(cat)">
          <span class="prompt">$cd {{ cat.slug }}</span>
          <div class="category-header">
            <span class="keyword">export</span>
            <span class="name">{{ cat.name }}</span>
            <span class="comment">// {{ cat.skill_count || 0 }} 个技能</span>
          </div>

          <!-- 子分类 -->
          <div v-if="cat.children && cat.children.length > 0 && expandedCategories.has(cat.id)" class="sub-categories">
            <div
              v-for="child in cat.children"
              :key="child.id"
              class="sub-category-item"
              @click.stop="viewCategory(child)"
            >
              <span class="filename">{{ child.slug }}.ts</span>
              <span class="keyword">import</span>
              <span class="name">{{ child.name }}</span>
              <span class="comment">// {{ child.skill_count || 0 }} 个技能</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Skills 列表 -->
      <div v-if="selectedCategory" class="skills-list">
        <div class="section-header">
          <span class="prompt">$ls skills/</span>
        </div>
        <div v-if="skills.length > 0">
          <div v-for="skill in skills" :key="skill.id" class="skill-item" @click="viewSkill(skill)">
            <span class="filename">{{ skill.directory }}/</span>
            <span class="keyword">const</span>
            <span class="name">{{ skill.name }}</span>
            <span class="comment">{{ skill.description ? '// ' + skill.description.substring(0, 50) : '' }}</span>
          </div>
        </div>
        <div v-else class="empty">
          <span class="comment">// No skills found</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../api'

const route = useRoute()
const router = useRouter()

const categories = ref<any[]>([])
const skills = ref<any[]>([])
const selectedCategory = ref<any>(null)
const loading = ref(true)
const expandedCategories = ref(new Set<number>())

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
  if (expandedCategories.value.has(cat.id)) {
    expandedCategories.value.delete(cat.id)
  } else {
    expandedCategories.value.add(cat.id)
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
.cli-terminal {
  min-height: 100vh;
  padding: 2rem;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

.terminal-header {
  margin-bottom: 2rem;
}

.prompt {
  color: #9aa5ce;
}

.cursor {
  color: #9aa5ce;
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

.filename {
  color: #7aa2f7;
}

.category-item {
  margin-bottom: 1rem;
  cursor: pointer;
}

.category-header {
  padding-left: 1rem;
}

.sub-categories {
  padding-left: 2rem;
  margin-top: 0.5rem;
}

.sub-category-item {
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.sub-category-item:hover .name {
  text-decoration: underline;
}

.skills-list {
  margin-top: 2rem;
}

.section-header {
  margin-bottom: 1rem;
}

.skill-item {
  padding-left: 1rem;
  margin-bottom: 0.5rem;
  cursor: pointer;
}

.skill-item:hover .name {
  text-decoration: underline;
}

.empty {
  padding-left: 1rem;
}

.loading {
  padding: 1rem;
}
</style>
