<template>
  <div class="category-item" :style="{ paddingLeft: level * 1.5 + 'rem' }">
    <div
      class="category-header"
      :class="{ 'selectable': selectable, 'selected': isSelected }"
      @click="handleClick"
    >
      <span v-if="selectable" class="checkbox">
        <input type="checkbox" :checked="isSelected" @change="$emit('select', category)" @click.stop />
      </span>
      <span v-else class="prompt" @click.stop="toggleExpand">{{ expanded ? '▼' : '▶' }}</span>
      <span class="keyword">{{ category.parent_id ? '├──' : '┬──' }}</span>
      <span class="name">{{ category.name }}</span>
      <span class="slug">({{ category.slug }})</span>
      <span class="comment">// {{ category.skill_count || 0 }} skills</span>

      <div v-if="!selectable" class="category-actions" @click.stop>
        <button @click="$emit('edit', category)" class="action-btn">
          <span class="keyword">$edit</span>
        </button>
        <button @click="$emit('delete', category)" class="action-btn danger">
          <span class="keyword">$rm</span>
        </button>
      </div>
    </div>

    <!-- 子分类 -->
    <div v-if="expanded && category.children && category.children.length > 0" class="children">
      <CategoryItem
        v-for="child in category.children"
        :key="child.id"
        :category="child"
        :level="level + 1"
        :selectable="selectable"
        :is-selected="isChildSelected(child.id)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  category: any
  level: number
  selectable?: boolean
  isSelected?: boolean
}>()

defineEmits<{
  edit: [category: any]
  delete: [category: any]
  select: [category: any]
}>()

const expanded = ref(true)

function toggleExpand() {
  expanded.value = !expanded.value
}

function handleClick() {
  if (!selectable) {
    toggleExpand()
  }
}

// 简化子项选中状态处理（父组件通过 isSelected prop 传递）
function isChildSelected(childId: number): boolean {
  return false
}
</script>

<style scoped>
.category-item {
  margin-bottom: 0.5rem;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  padding: 0.25rem 0;
  border-radius: 4px;
}

.category-header:hover {
  background: rgba(122, 162, 247, 0.1);
}

.category-header.selectable:hover {
  background: rgba(122, 162, 247, 0.15);
}

.category-header.selected {
  background: rgba(122, 162, 247, 0.2);
}

.checkbox {
  display: flex;
  align-items: center;
  min-width: 20px;
}

.checkbox input {
  width: 16px;
  height: 16px;
  accent-color: #7aa2f7;
  cursor: pointer;
}

.prompt {
  color: #9aa5ce;
  font-size: 0.8rem;
}

.keyword {
  color: #bb9af7;
}

.name {
  color: #7dcfff;
}

.slug {
  color: #565f89;
}

.comment {
  color: #565f89;
  margin-left: auto;
  margin-right: 1rem;
}

.category-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  color: #7aa2f7;
  font-family: inherit;
  font-size: 0.8rem;
}

.action-btn.danger {
  color: #f7768e;
}

.children {
  margin-top: 0.25rem;
}
</style>
