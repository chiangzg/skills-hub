<template>
  <div class="category-item" :style="{ paddingLeft: level * 1.5 + 'rem' }">
    <div class="category-header" @click="toggleExpand">
      <span class="prompt">{{ expanded ? '▼' : '▶' }}</span>
      <span class="keyword">{{ category.parent_id ? '├──' : '┬──' }}</span>
      <span class="name">{{ category.name }}</span>
      <span class="slug">({{ category.slug }})</span>
      <span class="comment">// {{ category.skill_count || 0 }} skills</span>

      <div class="category-actions" @click.stop>
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
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  category: any
  level: number
}>()

defineEmits<{
  edit: [category: any]
  delete: [category: any]
}>()

const expanded = ref(true)

function toggleExpand() {
  expanded.value = !expanded.value
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
}

.category-header:hover {
  background: rgba(122, 162, 247, 0.1);
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
