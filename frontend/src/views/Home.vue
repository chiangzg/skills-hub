<template>
  <div class="home-page">
    <header class="top-bar">
      <div class="top-inner">
        <p class="top-note">Skills Hub · 内部技能生态</p>
        <nav class="top-links">
          <button class="link-btn" @click="$router.push('/categories')">分类浏览</button>
          <button class="link-btn" @click="$router.push('/admin')">管理后台</button>
        </nav>
      </div>
    </header>

    <section class="hero">
      <div class="hero-inner">
        <p class="hero-badge">Discover · Rank · Reuse</p>
        <h1 class="hero-title">Skills Hub</h1>
        <p class="hero-subtitle">东福Skill生态系统。</p>
        <div class="hero-actions">
          <button class="primary-btn" @click="scrollToBoard">浏览技能榜</button>
          <button class="ghost-btn" @click="$router.push('/categories')">进入分类页</button>
        </div>
      </div>
    </section>

    <section class="board" ref="boardRef">
      <div class="board-controls">
        <div class="search-wrap">
          <input
            v-model="searchInput"
            class="search-input"
            type="text"
            placeholder="搜索技能名称或描述..."
          />
        </div>

        <div class="tab-group">
          <button
            v-for="tab in rankTabs"
            :key="tab.value"
            class="tab-btn"
            :class="{ active: activeTab === tab.value }"
            @click="setTab(tab.value)"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="summary">
          <span>命中 {{ total }} 个技能</span>
          <span v-if="selectedCategory">分类：{{ selectedCategory.name }}</span>
          <span v-if="searchKeyword">关键词：{{ searchKeyword }}</span>
        </div>
      </div>

      <div class="board-layout" v-if="!initialLoading">
        <CategorySidebar
          :categories="categories"
          :selectedSlug="selectedCategorySlug"
          :mobileOpen="mobileFilterOpen"
          @select="selectCategory"
          @clear="clearCategory"
        />

        <main class="rank-main">
          <div class="mobile-filter-row">
            <button class="mobile-filter-btn" @click="mobileFilterOpen = !mobileFilterOpen">
              {{ mobileFilterOpen ? '收起分类' : '展开分类' }}
            </button>
          </div>

          <div v-if="loadingSkills" class="state-card">加载技能榜中...</div>
          <div v-else-if="loadError" class="state-card error">{{ loadError }}</div>
          <div v-else-if="skills.length === 0" class="state-card">暂无匹配技能</div>

          <div v-else class="table-wrap">
            <table class="rank-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Skill</th>
                  <th>分类</th>
                  <th>热度</th>
                  <th>Stars</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(skill, index) in skills"
                  :key="skill.id"
                  class="rank-row"
                  @click="goSkill(skill.id)"
                >
                  <td>{{ rankStart + index + 1 }}</td>
                  <td>
                    <div class="skill-cell">
                      <p class="skill-name">{{ skill.name }}</p>
                      <p class="skill-repo">{{ skill.repository?.full_name || '-' }}</p>
                    </div>
                  </td>
                  <td>
                    <div class="chips">
                      <span
                        v-for="cat in (skill.categories || []).slice(0, 2)"
                        :key="`${skill.id}-${cat.id}`"
                        class="chip"
                      >
                        {{ cat.name }}
                      </span>
                      <span v-if="(skill.categories || []).length === 0" class="chip muted">未分类</span>
                    </div>
                  </td>
                  <td>{{ skill.views || 0 }}</td>
                  <td>{{ skill.stars || 0 }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="totalPages > 1" class="pager">
            <button class="pager-btn" :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">
              上一页
            </button>
            <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button
              class="pager-btn"
              :disabled="currentPage >= totalPages"
              @click="changePage(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </main>
      </div>

      <div v-else class="state-card">加载首页中...</div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api, skillApi } from '../api'
import CategorySidebar, { type CategoryItem } from '../components/CategorySidebar.vue'

type RankTab = 'all' | 'trending' | 'starred'

const route = useRoute()
const router = useRouter()
const boardRef = ref<HTMLElement | null>(null)

const categories = ref<CategoryItem[]>([])
const skills = ref<any[]>([])
const selectedCategorySlug = ref('all')
const activeTab = ref<RankTab>('all')
const searchInput = ref('')
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = 20
const total = ref(0)
const totalPages = ref(1)

const initialLoading = ref(true)
const loadingSkills = ref(false)
const loadError = ref('')
const mobileFilterOpen = ref(false)

const rankTabs = [
  { value: 'all', label: '全量榜' },
  { value: 'trending', label: '近期活跃' },
  { value: 'starred', label: '高星技能' }
] as const

let searchDebounceTimer: ReturnType<typeof setTimeout> | null = null
let syncingQuery = false
const initialized = ref(false)

const flatCategories = computed(() => {
  const all: CategoryItem[] = []
  for (const root of categories.value) {
    all.push(root)
    all.push(...root.children)
  }
  return all
})

const selectedCategory = computed(() => {
  if (selectedCategorySlug.value === 'all') return null
  return flatCategories.value.find((item) => item.slug === selectedCategorySlug.value) || null
})

const selectedCategoryId = computed(() => selectedCategory.value?.id)
const rankStart = computed(() => (currentPage.value - 1) * pageSize)

onMounted(async () => {
  await loadCategories()
  applyQueryToState(route.query)
  await fetchSkills()
  initialized.value = true
  initialLoading.value = false
})

onBeforeUnmount(() => {
  if (searchDebounceTimer) {
    clearTimeout(searchDebounceTimer)
    searchDebounceTimer = null
  }
})

watch(searchInput, (value) => {
  if (!initialized.value) return
  if (searchDebounceTimer) clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    searchKeyword.value = value.trim()
    currentPage.value = 1
  }, 300)
})

watch([activeTab, selectedCategorySlug, searchKeyword, currentPage], async () => {
  if (!initialized.value) return
  await syncQueryFromState()
  await fetchSkills()
})

watch(
  () => route.query,
  async (query) => {
    if (!initialized.value || syncingQuery) return
    const before = buildQueryFromState()
    applyQueryToState(query)
    const after = buildQueryFromState()
    if (JSON.stringify(before) !== JSON.stringify(after)) {
      await fetchSkills()
    }
  }
)

async function loadCategories() {
  try {
    const list = await api.get('/categories') as any[]
    categories.value = buildCategoryTree(list)
  } catch {
    categories.value = []
  }
}

function buildCategoryTree(items: any[]): CategoryItem[] {
  const map = new Map<number, CategoryItem>()

  for (const raw of items) {
    map.set(raw.id, {
      id: raw.id,
      parent_id: raw.parent_id,
      name: raw.name,
      slug: raw.slug,
      sort_order: raw.sort_order || 0,
      skill_count: raw.skill_count || 0,
      children: []
    })
  }

  const roots: CategoryItem[] = []
  for (const node of map.values()) {
    if (node.parent_id && map.has(node.parent_id)) {
      map.get(node.parent_id)?.children.push(node)
    } else {
      roots.push(node)
    }
  }

  const sortNodes = (nodes: CategoryItem[]) => {
    nodes.sort((a, b) => a.sort_order - b.sort_order)
    for (const node of nodes) {
      if (node.children.length > 0) sortNodes(node.children)
    }
  }

  sortNodes(roots)
  return roots
}

function normalizeTab(value: unknown): RankTab {
  return value === 'trending' || value === 'starred' ? value : 'all'
}

function normalizeCategorySlug(value: unknown): string {
  if (typeof value !== 'string' || value.trim() === '') return 'all'
  return flatCategories.value.some((item) => item.slug === value) ? value : 'all'
}

function normalizePage(value: unknown): number {
  const parsed = Number(value)
  if (!Number.isInteger(parsed) || parsed < 1) return 1
  return parsed
}

function applyQueryToState(query: Record<string, any>) {
  const q = typeof query.q === 'string' ? query.q.trim() : ''
  searchInput.value = q
  searchKeyword.value = q
  activeTab.value = normalizeTab(query.tab)
  selectedCategorySlug.value = normalizeCategorySlug(query.category)
  currentPage.value = normalizePage(query.page)
}

function buildQueryFromState() {
  const query: Record<string, string> = {}
  if (searchKeyword.value) query.q = searchKeyword.value
  if (activeTab.value !== 'all') query.tab = activeTab.value
  if (selectedCategorySlug.value !== 'all') query.category = selectedCategorySlug.value
  if (currentPage.value > 1) query.page = String(currentPage.value)
  return query
}

async function syncQueryFromState() {
  const target = buildQueryFromState()
  const current = {
    q: typeof route.query.q === 'string' ? route.query.q : undefined,
    tab: typeof route.query.tab === 'string' ? route.query.tab : undefined,
    category: typeof route.query.category === 'string' ? route.query.category : undefined,
    page: typeof route.query.page === 'string' ? route.query.page : undefined
  }

  if (JSON.stringify(target) === JSON.stringify(compactQuery(current))) return

  syncingQuery = true
  try {
    await router.replace({ query: target })
  } finally {
    syncingQuery = false
  }
}

function compactQuery(query: Record<string, string | undefined>) {
  const compact: Record<string, string> = {}
  for (const [key, value] of Object.entries(query)) {
    if (value) compact[key] = value
  }
  return compact
}

function getSort(tab: RankTab) {
  if (tab === 'trending') return { sort_by: 'updated_at', sort_order: 'desc' }
  if (tab === 'starred') return { sort_by: 'stars', sort_order: 'desc' }
  return { sort_by: 'views', sort_order: 'desc' }
}

async function fetchSkills() {
  loadingSkills.value = true
  loadError.value = ''

  try {
    const sort = getSort(activeTab.value)
    const response = await skillApi.list({
      keyword: searchKeyword.value || undefined,
      category_id: selectedCategoryId.value,
      page: currentPage.value,
      page_size: pageSize,
      sort_by: sort.sort_by,
      sort_order: sort.sort_order
    }) as any

    skills.value = response.items || []
    total.value = response.total || 0
    totalPages.value = response.total_pages || 1

    if (currentPage.value > totalPages.value && totalPages.value > 0) {
      currentPage.value = totalPages.value
    }
  } catch {
    skills.value = []
    total.value = 0
    totalPages.value = 1
    loadError.value = '加载失败，请稍后重试。'
  } finally {
    loadingSkills.value = false
  }
}

function setTab(tab: RankTab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  currentPage.value = 1
}

function selectCategory(slug: string) {
  if (selectedCategorySlug.value === slug) return
  selectedCategorySlug.value = slug
  currentPage.value = 1
  mobileFilterOpen.value = false
}

function clearCategory() {
  selectCategory('all')
}

function changePage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
}

function goSkill(id: number) {
  router.push(`/skills/${id}`)
}

function scrollToBoard() {
  boardRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: radial-gradient(circle at top, #202540 0%, var(--bg-primary) 45%);
  color: var(--text-primary);
}

.top-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border-light);
  background: rgba(15, 15, 26, 0.85);
}

.top-inner {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0.7rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.top-note {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.top-links {
  display: flex;
  gap: 0.5rem;
}

.link-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  padding: 0.35rem 0.65rem;
  border-radius: 8px;
  cursor: pointer;
}

.link-btn:hover {
  color: var(--text-primary);
  border-color: var(--brand-cyan);
}

.hero {
  padding: 4.5rem 1.25rem 3rem;
}

.hero-inner {
  max-width: 1280px;
  margin: 0 auto;
}

.hero-badge {
  width: fit-content;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: rgba(122, 162, 247, 0.16);
  border: 1px solid rgba(122, 162, 247, 0.3);
  color: var(--brand-cyan);
  font-size: 0.8rem;
  margin-bottom: 1rem;
}

.hero-title {
  font-size: clamp(2.1rem, 4vw, 3.6rem);
  line-height: 1.1;
  margin-bottom: 0.9rem;
}

.hero-subtitle {
  max-width: 740px;
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
}

.hero-actions {
  display: flex;
  gap: 0.75rem;
}

.primary-btn,
.ghost-btn {
  border-radius: 10px;
  padding: 0.65rem 1rem;
  cursor: pointer;
  font-weight: 600;
}

.primary-btn {
  border: none;
  color: #fff;
  background: linear-gradient(135deg, var(--brand-blue), var(--brand-purple));
}

.ghost-btn {
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  background: transparent;
}

.board {
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 1.25rem 2rem;
}

.board-controls {
  margin-bottom: 1rem;
}

.search-wrap {
  margin-bottom: 0.75rem;
}

.search-input {
  width: 100%;
  border: 1px solid var(--border-color);
  background: rgba(26, 27, 38, 0.9);
  color: var(--text-primary);
  border-radius: 10px;
  padding: 0.8rem 0.9rem;
  font-size: 0.95rem;
}

.tab-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-bottom: 0.75rem;
}

.tab-btn {
  border: 1px solid var(--border-color);
  background: rgba(26, 27, 38, 0.7);
  color: var(--text-secondary);
  padding: 0.45rem 0.8rem;
  border-radius: 999px;
  cursor: pointer;
}

.tab-btn.active {
  border-color: var(--brand-cyan);
  color: #fff;
  background: rgba(122, 162, 247, 0.25);
}

.summary {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.board-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 1rem;
}

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
  cursor: pointer;
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

.count {
  font-size: 0.8rem;
  color: var(--text-tertiary);
}

.rank-main {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 0.9rem;
  background: rgba(18, 19, 30, 0.8);
}

.mobile-filter-row {
  display: none;
  margin-bottom: 0.7rem;
}

.mobile-filter-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 8px;
  padding: 0.45rem 0.65rem;
  cursor: pointer;
}

.state-card {
  border: 1px dashed var(--border-color);
  border-radius: 10px;
  padding: 1.2rem;
  text-align: center;
  color: var(--text-secondary);
}

.state-card.error {
  color: var(--brand-red);
}

.table-wrap {
  overflow-x: auto;
}

.rank-table {
  width: 100%;
  border-collapse: collapse;
}

.rank-table th,
.rank-table td {
  padding: 0.7rem 0.6rem;
  border-bottom: 1px solid var(--border-light);
  text-align: left;
  vertical-align: top;
  font-size: 0.9rem;
}

.rank-table th {
  color: var(--text-tertiary);
  font-weight: 500;
}

.rank-row {
  cursor: pointer;
  transition: background var(--transition-fast);
}

.rank-row:hover {
  background: rgba(122, 162, 247, 0.08);
}

.skill-cell {
  min-width: 260px;
}

.skill-name {
  color: var(--text-primary);
  font-weight: 600;
}

.skill-repo {
  color: var(--text-tertiary);
  font-size: 0.78rem;
  margin-top: 0.15rem;
}

.chips {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.chip {
  border: 1px solid rgba(125, 207, 255, 0.35);
  background: rgba(125, 207, 255, 0.12);
  color: var(--brand-cyan);
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  font-size: 0.72rem;
}

.chip.muted {
  border-color: var(--border-color);
  color: var(--text-tertiary);
  background: transparent;
}

.pager {
  margin-top: 0.95rem;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.65rem;
  font-size: 0.88rem;
  color: var(--text-secondary);
}

.pager-btn {
  border: 1px solid var(--border-color);
  background: transparent;
  color: var(--text-secondary);
  border-radius: 7px;
  padding: 0.4rem 0.7rem;
  cursor: pointer;
}

.pager-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 960px) {
  .board-layout {
    grid-template-columns: 1fr;
  }

  .category-sidebar {
    position: static;
    display: none;
  }

  .category-sidebar.open {
    display: block;
  }

  .mobile-filter-row {
    display: block;
  }
}

@media (max-width: 640px) {
  .hero {
    padding-top: 3rem;
  }

  .hero-actions {
    flex-wrap: wrap;
  }

  .rank-table th:nth-child(3),
  .rank-table td:nth-child(3) {
    display: none;
  }
}
</style>
