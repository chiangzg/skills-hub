<template>
  <div class="category-panel">
    <div class="panel-header">
      <span class="prompt">$cat categories.config</span>
      <button @click="showAddDialog = true" class="add-btn">
        <span class="keyword">$mkdir</span>
        <span class="name">new</span>
      </button>
    </div>

    <!-- 分类树 -->
    <div class="category-tree">
      <CategoryItem
        v-for="cat in categories"
        :key="cat.id"
        :category="cat"
        :level="0"
        @edit="editCategory"
        @delete="deleteCategory"
      />
    </div>

    <!-- 添加分类对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay" @click.self="showAddDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span class="prompt">$mkdir new</span>
        </div>
        <form @submit.prevent="addCategory" class="dialog-form">
          <div class="form-row">
            <label class="label">
              <span class="keyword">name</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.name" class="input" placeholder="分类名称" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">slug</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.slug" class="input" placeholder="category-slug" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">parent</span>
              <span class="punctuation">:</span>
            </label>
            <select v-model="form.parent_id" class="input">
              <option :value="null">无（顶级分类）</option>
              <option v-for="cat in flatCategories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">icon</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.icon" class="input" placeholder="icon" />
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
import { ref, onMounted, computed } from 'vue'
import { categoryApi } from '../../api'
import CategoryItem from './CategoryItem.vue'

const categories = ref<any[]>([])
const flatCategories = ref<any[]>([])
const showAddDialog = ref(false)
const loading = ref(false)

const form = ref({
  name: '',
  slug: '',
  parent_id: null as number | null,
  icon: ''
})

onMounted(async () => {
  await loadCategories()
})

async function loadCategories() {
  try {
    const data = await categoryApi.getTree()
    categories.value = data
    flatCategories.value = flattenCategories(data)
  } catch (e) {
    console.error('Failed to load categories:', e)
  }
}

function flattenCategories(cats: any[]): any[] {
  const result: any[] = []
  function flatten(list: any[]) {
    for (const cat of list) {
      result.push(cat)
      if (cat.children) {
        flatten(cat.children)
      }
    }
  }
  flatten(cats)
  return result
}

async function addCategory() {
  loading.value = true
  try {
    await categoryApi.create({
      name: form.value.name,
      slug: form.value.slug,
      parent_id: form.value.parent_id,
      icon: form.value.icon
    })
    showAddDialog.value = false
    form.value = { name: '', slug: '', parent_id: null, icon: '' }
    await loadCategories()
  } catch (e: any) {
    alert(e.message || '添加失败')
  } finally {
    loading.value = false
  }
}

function editCategory(cat: any) {
  // TODO: 实现编辑功能
  alert('编辑功能待实现')
}

async function deleteCategory(cat: any) {
  if (!confirm(`确定删除分类 ${cat.name}？`)) return

  try {
    await categoryApi.delete(cat.id)
    await loadCategories()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}
</script>

<style scoped>
.category-panel {
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

.add-btn {
  background: transparent;
  border: 1px solid #7aa2f7;
  color: #7aa2f7;
  cursor: pointer;
  padding: 0.5rem 1rem;
  font-family: inherit;
}

.category-tree {
  padding: 1rem 0;
}

/* 对话框样式同 RepositoryPanel */
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
