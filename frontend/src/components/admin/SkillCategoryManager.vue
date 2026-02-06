<template>
  <div class="skill-category-manager">
    <div class="panel-header">
      <span class="prompt">$cat skill-categories.config</span>
      <div class="header-actions">
        <button @click="refreshData" class="refresh-btn">
          <span class="keyword">$refresh</span>
        </button>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="manager-content">
      <!-- Skill选择区域 -->
      <div class="skills-section">
        <div class="section-header">
          <h3>技能列表</h3>
          <div class="search-bar">
            <input 
              v-model="skillSearch" 
              type="text" 
              placeholder="搜索技能..." 
              class="search-input"
            />
            <button @click="clearSkillSearch" class="clear-btn">✕</button>
          </div>
        </div>
        
        <div class="skills-list">
          <div 
            v-for="skill in filteredSkills" 
            :key="skill.id"
            :class="['skill-item', { selected: selectedSkills.includes(skill.id) }]"
            @click="toggleSkillSelection(skill.id)"
          >
            <div class="skill-checkbox">
              <input 
                type="checkbox" 
                :checked="selectedSkills.includes(skill.id)" 
                @change="toggleSkillSelection(skill.id)"
              />
            </div>
            <div class="skill-info">
              <div class="skill-name">{{ skill.name }}</div>
              <div class="skill-description">{{ skill.description || '无描述' }}</div>
              <div class="skill-meta">
                <span class="repo">{{ skill.repository }}</span>
                <span class="directory">{{ skill.directory }}</span>
              </div>
            </div>
          </div>
          
          <div v-if="filteredSkills.length === 0" class="no-data">
            没有找到匹配的技能
          </div>
        </div>
      </div>

      <!-- 分类选择区域 -->
      <div class="categories-section">
        <div class="section-header">
          <h3>分类选择</h3>
          <div class="selection-info">
            已选 {{ selectedCategories.length }} 个分类
          </div>
        </div>
        
        <div class="categories-tree">
          <CategoryItem
            v-for="cat in flatCategories"
            :key="cat.id"
            :category="cat"
            :level="getCategoryLevel(cat)"
            :is-selected="selectedCategories.includes(cat.id)"
            @select="toggleCategorySelection(cat.id)"
          />
        </div>
      </div>

      <!-- 操作区域 -->
      <div class="actions-section">
        <div class="action-buttons">
          <button 
            @click="assignCategories" 
            :disabled="selectedSkills.length === 0 || selectedCategories.length === 0"
            class="assign-btn"
          >
            <span class="keyword">$assign</span>
            <span class="name">绑定分类</span>
          </button>
          
          <button 
            @click="removeCategories" 
            :disabled="selectedSkills.length === 0 || selectedCategories.length === 0"
            class="remove-btn"
          >
            <span class="keyword">$remove</span>
            <span class="name">解绑分类</span>
          </button>
        </div>
        
        <div class="operation-status" v-if="operationStatus">
          <div :class="['status-message', operationStatus.type]">
            {{ operationStatus.message }}
          </div>
        </div>
      </div>
    </div>

    <!-- 批量操作确认对话框 -->
    <div v-if="showConfirmDialog" class="dialog-overlay" @click.self="showConfirmDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span class="prompt">$confirm</span>
        </div>
        <div class="dialog-content">
          <p>确认将 {{ selectedSkills.length }} 个技能绑定到 {{ selectedCategories.length }} 个分类？</p>
          <div class="dialog-actions">
            <button @click="showConfirmDialog = false" class="cancel-btn">
              <span class="keyword">$cancel</span>
            </button>
            <button @click="confirmOperation" class="submit-btn">
              <span class="keyword">$exec</span>
              <span class="name">确认</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { categoryApi, skillApi } from '../../api'
import CategoryItem from './CategoryItem.vue'

// 状态变量
const skills = ref<any[]>([])
const categories = ref<any[]>([])
const flatCategories = ref<any[]>([])
const selectedSkills = ref<number[]>([])
const selectedCategories = ref<number[]>([])
const skillSearch = ref('')
const operationStatus = ref<{type: 'success' | 'error', message: string} | null>(null)
const showConfirmDialog = ref(false)
const currentOperation = ref<'assign' | 'remove' | null>(null)

// 初始化数据
onMounted(async () => {
  await loadData()
})

// 加载数据
async function loadData() {
  try {
    // 加载所有技能（包括未分类的）
    const allSkills = await skillApi.list({ page_size: 100 })
    skills.value = allSkills.items
    
    // 加载分类树
    const categoryTree = await categoryApi.getTree()
    categories.value = categoryTree
    flatCategories.value = flattenCategories(categoryTree)
  } catch (e) {
    console.error('Failed to load data:', e)
    showStatus('error', '加载数据失败')
  }
}

// 平铺分类树
function flattenCategories(cats: any[]): any[] {
  const result: any[] = []
  function flatten(list: any[], level = 0) {
    for (const cat of list) {
      cat.level = level
      result.push(cat)
      if (cat.children && cat.children.length > 0) {
        flatten(cat.children, level + 1)
      }
    }
  }
  flatten(cats)
  return result
}

// 获取分类层级
function getCategoryLevel(cat: any): number {
  return cat.level || 0
}

// 过滤技能
const filteredSkills = computed(() => {
  if (!skillSearch.value) return skills.value
  
  const searchLower = skillSearch.value.toLowerCase()
  return skills.value.filter(skill => 
    skill.name.toLowerCase().includes(searchLower) || 
    (skill.description && skill.description.toLowerCase().includes(searchLower)) ||
    (skill.repository && skill.repository.toLowerCase().includes(searchLower))
  )
})

// 清除搜索
function clearSkillSearch() {
  skillSearch.value = ''
}

// 技能选择切换
function toggleSkillSelection(skillId: number) {
  const index = selectedSkills.value.indexOf(skillId)
  if (index === -1) {
    selectedSkills.value.push(skillId)
  } else {
    selectedSkills.value.splice(index, 1)
  }
}

// 分类选择切换
function toggleCategorySelection(catId: number) {
  const index = selectedCategories.value.indexOf(catId)
  if (index === -1) {
    selectedCategories.value.push(catId)
  } else {
    selectedCategories.value.splice(index, 1)
  }
}

// 绑定分类
function assignCategories() {
  if (selectedSkills.value.length === 0 || selectedCategories.value.length === 0) return
  
  currentOperation.value = 'assign'
  showConfirmDialog.value = true
}

// 解绑分类
function removeCategories() {
  if (selectedSkills.value.length === 0 || selectedCategories.value.length === 0) return
  
  currentOperation.value = 'remove'
  showConfirmDialog.value = true
}

// 确认操作
async function confirmOperation() {
  showConfirmDialog.value = false
  showStatus('info', '正在处理...')
  
  try {
    if (currentOperation.value === 'assign') {
      // 批量绑定分类
      const promises = selectedSkills.value.map(skillId => 
        categoryApi.assignSkill(skillId, selectedCategories.value)
      )
      await Promise.all(promises)
      showStatus('success', `成功绑定 ${selectedSkills.value.length} 个技能到 ${selectedCategories.value.length} 个分类`)
    } else if (currentOperation.value === 'remove') {
      // 批量解绑分类
      const promises = selectedSkills.value.map(skillId => 
        selectedCategories.value.map(catId => 
          categoryApi.removeSkill(catId, skillId)
        )
      ).flat()
      await Promise.all(promises)
      showStatus('success', `成功解绑 ${selectedSkills.value.length} 个技能与 ${selectedCategories.value.length} 个分类的关系`)
    }
    
    // 刷新数据
    await loadData()
    selectedSkills.value = []
    selectedCategories.value = []
  } catch (e: any) {
    showStatus('error', e.message || '操作失败')
    console.error('Operation failed:', e)
  }
}

// 显示状态消息
function showStatus(type: 'success' | 'error' | 'info', message: string) {
  operationStatus.value = { type, message }
  
  // 3秒后清除状态
  setTimeout(() => {
    operationStatus.value = null
  }, 3000)
}

// 刷新数据
function refreshData() {
  loadData()
}
</script>

<style scoped>
.skill-category-manager {
  padding: 1rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.refresh-btn {
  background: transparent;
  border: 1px solid #7aa2f7;
  color: #7aa2f7;
  cursor: pointer;
  padding: 0.5rem 1rem;
  font-family: inherit;
}

.manager-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.skills-section,
.categories-section {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h3 {
  color: var(--text-primary);
  margin: 0;
  font-size: 1.25rem;
}

.search-bar {
  display: flex;
  gap: 0.5rem;
}

.search-input {
  flex: 1;
  background: #16161e;
  border: 1px solid #414868;
  color: #c0caf5;
  padding: 0.5rem 1rem;
  font-family: inherit;
  border-radius: 6px;
}

.clear-btn {
  background: transparent;
  border: none;
  color: #9aa5ce;
  cursor: pointer;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.selection-info {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.skills-list {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.skill-item {
  display: flex;
  align-items: flex-start;
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--transition-fast);
  margin-bottom: 0.5rem;
  background: rgba(21, 22, 34, 0.5);
}

.skill-item:hover {
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid #7aa2f7;
}

.skill-item.selected {
  background: rgba(122, 162, 247, 0.2);
  border: 1px solid #7aa2f7;
}

.skill-checkbox {
  margin-right: 0.75rem;
  flex-shrink: 0;
}

.skill-checkbox input {
  width: 18px;
  height: 18px;
  accent-color: #7aa2f7;
}

.skill-info {
  flex: 1;
}

.skill-name {
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.skill-description {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.skill-meta {
  display: flex;
  gap: 0.75rem;
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.repo, .directory {
  background: rgba(122, 162, 247, 0.1);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.no-data {
  text-align: center;
  color: var(--text-tertiary);
  padding: 2rem;
}

.categories-tree {
  max-height: 500px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.actions-section {
  grid-column: 1 / span 2;
  background: rgba(26, 27, 38, 0.7);
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
}

.action-buttons {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.assign-btn,
.remove-btn {
  flex: 1;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-family: inherit;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.assign-btn {
  background: linear-gradient(135deg, #7aa2f7, #bb9af7);
  color: #1a1b26;
  border: none;
}

.remove-btn {
  background: linear-gradient(135deg, #f7768e, #ca789d);
  color: #1a1b26;
  border: none;
}

.assign-btn:disabled,
.remove-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.operation-status {
  margin-top: 1rem;
}

.status-message {
  padding: 0.75rem;
  border-radius: 8px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-message.success {
  background: rgba(94, 234, 178, 0.1);
  color: #5ee2b2;
  border: 1px solid rgba(94, 234, 178, 0.3);
}

.status-message.error {
  background: rgba(247, 118, 142, 0.1);
  color: #f7768e;
  border: 1px solid rgba(247, 118, 142, 0.3);
}

.status-message.info {
  background: rgba(122, 162, 247, 0.1);
  color: #7aa2f7;
  border: 1px solid rgba(122, 162, 247, 0.3);
}

/* 对话框样式 */
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
  border-radius: 12px;
}

.dialog-header {
  margin-bottom: 1.5rem;
}

.dialog-content {
  margin-bottom: 1.5rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.cancel-btn,
.submit-btn {
  padding: 0.5rem 1rem;
  font-family: inherit;
  cursor: pointer;
  border-radius: 6px;
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

/* 响应式设计 */
@media (max-width: 768px) {
  .manager-content {
    grid-template-columns: 1fr;
  }
  
  .actions-section {
    grid-column: 1;
  }
}
</style>