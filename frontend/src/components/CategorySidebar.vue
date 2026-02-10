<template>
  <aside class="category-sidebar" :class="{ open: mobileOpen }">
    <div class="sidebar-head">
      <h2>{{ title }}</h2>
      <button v-if="showClearButton" class="clear-btn" @click="handleClear">
        清空
      </button>
    </div>

    <!-- 全部分类选项 -->
    <button
      v-if="showAllOption"
      class="category-item root"
      :class="{ active: isSelected('all') }"
      @click="handleSelect('all')"
    >
      <span>全部分类</span>
    </button>

    <!-- 分类树 -->
    <div v-for="root in categories" :key="root.id" class="category-block">
      <div
        class="category-item root"
        :class="{ active: isSelected(root.slug) }"
      >
        <button class="name-btn" @click.stop="handleSelect(root.slug)">
          {{ root.name }}
        </button>
        <div class="right-actions">
          <span class="count">{{ root.skill_count || 0 }}</span>
          <button
            v-if="root.children.length > 0"
            class="expand-btn"
            @click.stop="toggleExpand(root.id)"
          >
            {{ isExpanded(root.id) ? '−' : '+' }}
          </button>
        </div>
      </div>

      <div v-if="root.children.length > 0 && isExpanded(root.id)" class="children-list">
        <button
          v-for="child in root.children"
          :key="child.id"
          class="category-item child"
          :class="{ active: isSelected(child.slug) }"
          @click.stop="handleSelect(child.slug)"
        >
          <span>{{ child.name }}</span>
          <span class="count">{{ child.skill_count || 0 }}</span>
        </button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

export interface CategoryItem {
  id: number
  parent_id: number | null
  name: string
  slug: string
  sort_order: number
  skill_count: number
  children: CategoryItem[]
}

interface Props {
  categories: CategoryItem[]
  selectedSlug?: string
  showAllOption?: boolean
  initiallyExpanded?: boolean
  mobileOpen?: boolean
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedSlug: 'all',
  showAllOption: true,
  initiallyExpanded: true,
  mobileOpen: false,
  title: '分类筛选'
})

const emit = defineEmits<{
  select: [slug: string]
  clear: []
}>()

const expandedIds = ref<Set<number>>(new Set())

const showClearButton = computed(() => props.showAllOption && props.selectedSlug !== 'all')

function isExpanded(id: number): boolean {
  return expandedIds.value.has(id)
}

function isSelected(slug: string): boolean {
  return props.selectedSlug === slug
}

function toggleExpand(id: number) {
  if (expandedIds.value.has(id)) {
    expandedIds.value.delete(id)
  } else {
    expandedIds.value.add(id)
  }
}

function handleSelect(slug: string) {
  emit('select', slug)
}

function handleClear() {
  emit('clear')
}

// 初始化展开所有根分类
watch(
  () => props.categories,
  (categories) => {
    if (props.initiallyExpanded && categories.length > 0) {
      expandedIds.value = new Set(categories.map((item) => item.id))
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.category-sidebar {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 0.8rem;
  background: rgba(18, 19, 30, 0.85);
  height: fit-content;
  position: sticky;
  top: 66px;
}

.sidebar-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.sidebar-head h2 {
  font-size: 1rem;
}

.clear-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 6px;
  padding: 0.2rem 0.45rem;
  cursor: pointer;
}

.clear-btn:hover {
  border-color: var(--brand-cyan);
  color: var(--text-primary);
}

.category-block {
  margin-top: 0.45rem;
}

.category-item {
  width: 100%;
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 8px;
  padding: 0.45rem 0.55rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
  pointer-events: none;
}

.category-item > * {
  pointer-events: auto;
}

.category-item:hover {
  background: rgba(122, 162, 247, 0.08);
}

.category-item.active {
  border-color: rgba(122, 162, 247, 0.45);
  background: rgba(122, 162, 247, 0.14);
  color: #fff;
}

.category-item.root {
  font-weight: 600;
}

.category-item.child {
  padding-left: 1.4rem;
  margin-top: 0.2rem;
}

.name-btn {
  border: none;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.right-actions {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.expand-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 5px;
  width: 22px;
  height: 22px;
  line-height: 1;
  cursor: pointer;
}

.expand-btn:hover {
  border-color: var(--brand-cyan);
  color: var(--text-primary);
}

.count {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.children-list {
  display: flex;
  flex-direction: column;
}

/* 响应式 */
@media (max-width: 960px) {
  .category-sidebar {
    position: static;
    display: none;
  }

  .category-sidebar.open {
    display: block;
  }
}
</style>
