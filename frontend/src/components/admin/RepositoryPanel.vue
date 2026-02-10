<template>
  <div class="repository-panel">
    <div class="panel-header">
      <span class="prompt">$cat repositories.config</span>
      <button @click="showAddDialog = true" class="add-btn">
        <span class="keyword">$touch</span>
        <span class="name">new</span>
      </button>
    </div>

    <!-- 仓库列表 -->
    <div class="repo-list">
      <div
        v-for="repo in repositories"
        :key="repo.id"
        class="repo-item"
      >
        <div class="repo-info">
          <span class="keyword">{{ repo.type }}</span>
          <span class="name">{{ repo.owner }}/{{ repo.name }}</span>
          <span class="punctuation">:</span>
          <span class="string">{{ repo.branch }}</span>
          <span class="comment">// {{ repo.skill_count }} skills</span>
        </div>
        <div class="repo-actions">
          <button @click="openSyncConfirm(repo)" :disabled="repo.syncing" class="action-btn">
            <span class="keyword">$sync</span>
          </button>
          <button @click="editRepo(repo)" class="action-btn">
            <span class="keyword">$edit</span>
          </button>
          <button @click="deleteRepo(repo)" class="action-btn danger">
            <span class="keyword">$rm</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 添加仓库对话框 -->
    <div v-if="showAddDialog" class="dialog-overlay" @click.self="showAddDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span class="prompt">$touch new</span>
        </div>
        <form @submit.prevent="addRepo" class="dialog-form">
          <div class="form-row">
            <label class="label">
              <span class="keyword">type</span>
              <span class="punctuation">:</span>
            </label>
            <select v-model="form.type" class="input">
              <option value="github">github</option>
              <option value="gitlab">gitlab</option>
            </select>
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">owner</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.owner" class="input" placeholder="owner" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">name</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.name" class="input" placeholder="repository" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">branch</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.branch" class="input" placeholder="main" />
          </div>
          <div v-if="form.type === 'gitlab'" class="form-row">
            <label class="label">
              <span class="keyword">gitlab_url</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.gitlab_url" class="input" placeholder="https://gitlab.example.com or https://gitlab.example.com/owner/repo" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">token</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="form.access_token" class="input" type="password" placeholder="(optional)" />
          </div>
          <div class="dialog-actions">
            <button type="button" @click="showAddDialog = false" class="cancel-btn">
              <span class="keyword">$cancel</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="loading">
              <span class="keyword">$exec</span>
              <span class="name">add</span>
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 同步确认对话框 -->
    <div v-if="showSyncConfirm" class="dialog-overlay" @click.self="showSyncConfirm = false">
      <div class="dialog dialog-small">
        <div class="dialog-header">
          <span class="prompt">$sync --confirm</span>
        </div>
        <div class="dialog-body">
          <p>确定要同步仓库 <span class="string">{{ pendingSyncRepo?.owner }}/{{ pendingSyncRepo?.name }}</span> 吗？</p>
        </div>
        <div class="dialog-actions">
          <button @click="showSyncConfirm = false" class="cancel-btn">
            <span class="keyword">$cancel</span>
          </button>
          <button @click="confirmSync" class="submit-btn" :disabled="syncing">
            <span class="keyword">$exec</span>
            <span class="name">sync</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 编辑仓库对话框 -->
    <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
      <div class="dialog">
        <div class="dialog-header">
          <span class="prompt">$edit {{ editingRepo?.owner }}/{{ editingRepo?.name }}</span>
        </div>
        <form @submit.prevent="saveEdit" class="dialog-form">
          <div class="form-row">
            <label class="label">
              <span class="keyword">branch</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="editForm.branch" class="input" required />
          </div>
          <div v-if="editingRepo?.type === 'GITLAB'" class="form-row">
            <label class="label">
              <span class="keyword">gitlab_url</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="editForm.gitlab_url" class="input" />
          </div>
          <div class="form-row">
            <label class="label">
              <span class="keyword">access_token</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="editForm.access_token" class="input" type="password" placeholder="留空则不修改" />
          </div>
          <div class="form-row">
            <label class="label checkbox-label">
              <span class="keyword">enabled</span>
              <span class="punctuation">:</span>
            </label>
            <input v-model="editForm.enabled" type="checkbox" class="checkbox" />
            <span class="checkbox-text">{{ editForm.enabled ? 'true' : 'false' }}</span>
          </div>
          <div class="dialog-actions">
            <button type="button" @click="showEditDialog = false" class="cancel-btn">
              <span class="keyword">$cancel</span>
            </button>
            <button type="submit" class="submit-btn" :disabled="saving">
              <span class="keyword">$exec</span>
              <span class="name">save</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { repositoryApi } from '../../api'

const repositories = ref<any[]>([])
const showAddDialog = ref(false)
const showSyncConfirm = ref(false)
const showEditDialog = ref(false)
const loading = ref(false)
const syncing = ref(false)
const saving = ref(false)
const pendingSyncRepo = ref<any>(null)
const editingRepo = ref<any>(null)

const form = ref({
  type: 'github',
  owner: '',
  name: '',
  branch: 'main',
  gitlab_url: '',
  access_token: ''
})

const editForm = ref({
  branch: '',
  gitlab_url: '',
  access_token: '',
  enabled: true
})

onMounted(async () => {
  await loadRepositories()
})

async function loadRepositories() {
  try {
    repositories.value = await repositoryApi.list()
  } catch (e) {
    console.error('Failed to load repositories:', e)
  }
}

async function addRepo() {
  loading.value = true
  try {
    await repositoryApi.create({
      type: form.value.type,
      owner: form.value.owner,
      name: form.value.name,
      branch: form.value.branch,
      gitlab_url: form.value.gitlab_url || undefined,
      access_token: form.value.access_token || undefined
    })
    showAddDialog.value = false
    form.value = {
      type: 'github',
      owner: '',
      name: '',
      branch: 'main',
      gitlab_url: '',
      access_token: ''
    }
    await loadRepositories()
  } catch (e: any) {
    alert(e.message || '添加失败')
  } finally {
    loading.value = false
  }
}

function openSyncConfirm(repo: any) {
  pendingSyncRepo.value = repo
  showSyncConfirm.value = true
}

async function confirmSync() {
  if (!pendingSyncRepo.value) return

  syncing.value = true
  try {
    const result = await repositoryApi.sync(pendingSyncRepo.value.id)
    alert(`同步完成: ${result.message}`)
    await loadRepositories()
  } catch (e: any) {
    alert(e.message || '同步失败')
  } finally {
    syncing.value = false
    showSyncConfirm.value = false
    pendingSyncRepo.value = null
  }
}

function editRepo(repo: any) {
  editingRepo.value = repo
  editForm.value = {
    branch: repo.branch,
    gitlab_url: repo.gitlab_url || '',
    access_token: '',
    enabled: repo.enabled
  }
  showEditDialog.value = true
}

async function saveEdit() {
  if (!editingRepo.value) return

  saving.value = true
  try {
    const updateData: any = {
      branch: editForm.value.branch,
      enabled: editForm.value.enabled
    }

    if (editForm.value.gitlab_url && editingRepo.value.type === 'GITLAB') {
      updateData.gitlab_url = editForm.value.gitlab_url
    }

    if (editForm.value.access_token) {
      updateData.access_token = editForm.value.access_token
    }

    await repositoryApi.update(editingRepo.value.id, updateData)
    showEditDialog.value = false
    editingRepo.value = null
    await loadRepositories()
  } catch (e: any) {
    alert(e.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function deleteRepo(repo: any) {
  if (!confirm(`确定删除仓库 ${repo.full_name}？`)) return

  try {
    await repositoryApi.delete(repo.id)
    await loadRepositories()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}
</script>

<style scoped>
.repository-panel {
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

.string {
  color: #9ece6a;
}

.punctuation {
  color: #9aa5ce;
}

.comment {
  color: #565f89;
}

.add-btn {
  background: transparent;
  border: 1px solid #7aa2f7;
  color: #7aa2f7;
  cursor: pointer;
  padding: 0.5rem 1rem;
  font-family: inherit;
}

.repo-list {
  padding: 1rem 0;
}

.repo-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  border-bottom: 1px solid #414868;
}

.repo-info {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.repo-actions {
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
}

.action-btn.danger {
  color: #f7768e;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 对话框 */
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
  width: 120px;
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

/* 对话框内容 */
.dialog-body {
  margin-bottom: 1.5rem;
}

.dialog-body p {
  color: #c0caf5;
}

.dialog-small {
  min-width: 320px;
}

/* 复选框样式 */
.checkbox-label {
  display: flex;
  align-items: center;
}

.checkbox {
  width: auto;
  flex: 0;
  margin: 0 0.5rem 0 0;
  cursor: pointer;
}

.checkbox-text {
  color: #9ece6a;
}
</style>
