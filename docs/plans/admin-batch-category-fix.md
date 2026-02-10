# Admin 技能批量关联分类功能修复计划

## Context

用户反馈 admin 页面的"技能批量关联分类"功能存在问题：左侧可以选择技能，但右侧无法选择分类，也无法操作绑定和解绑。

### 问题根源

`SkillCategoryManager.vue` 使用 `CategoryItem.vue` 组件来渲染分类树，但 `CategoryItem` 组件不支持选择功能：

**SkillCategoryManager.vue (第 69-76 行)** 传递了以下 props 和事件：
```vue
<CategoryItem
  :is-selected="selectedCategories.includes(cat.id)"
  @select="toggleCategorySelection(cat.id)"
/>
```

**但 CategoryItem.vue 没有实现这些功能：**
- 没有 `is-selected` prop (只有 `category` 和 `level`)
- 没有 `select` 事件 (只有 `edit` 和 `delete`)
- 模板中没有复选框或选择 UI
- 点击事件被 `toggleExpand` 占用（展开/折叠功能）

---

## 实现方案

### 方案选择

**方案 A：** 修改 `CategoryItem` 组件支持选择模式
- 优点：复用现有组件
- 缺点：增加组件复杂度，选择模式和管理模式混合

**方案 B：** 创建新的 `SelectableCategoryItem` 组件
- 优点：职责清晰，不影响现有功能
- 缺点：代码重复

**推荐方案 A**：通过添加 `selectable` 和 `is-selected` props 来扩展 `CategoryItem` 组件，使其支持选择模式。

---

## 修改文件

### 1. `frontend/src/components/admin/CategoryItem.vue`

**添加选择支持的 props 和事件：**

```typescript
defineProps<{
  category: any
  level: number
  selectable?: boolean    // 新增：是否可选择模式
  isSelected?: boolean    // 新增：是否已选中
}>()

defineEmits<{
  edit: [category: any]
  delete: [category: any]
  select: [category: any]  // 新增：选择事件
  toggleExpand: [category: any]  // 新增：展开/折叠事件
}>()
```

**模板修改：**
- 添加复选框（当 `selectable=true` 时）
- 选择模式下点击整个项触发选中，而不是展开/折叠
- 选中状态添加视觉反馈

### 2. `frontend/src/components/admin/SkillCategoryManager.vue`

**更新 CategoryItem 调用 (第 69-76 行)：**

```vue
<CategoryItem
  v-for="cat in flatCategories"
  :key="cat.id"
  :category="cat"
  :level="getCategoryLevel(cat)"
  :selectable="true"
  :is-selected="selectedCategories.includes(cat.id)"
  @select="toggleCategorySelection(cat.id)"
/>
```

**同时修复 API 返回值问题 (第 158-159 行)：**

当前代码假设 `skillApi.list` 返回 `{ items: [...] }`，但实际返回的是数组。

修改为：
```typescript
const allSkills = await skillApi.list({ page_size: 100 })
skills.value = Array.isArray(allSkills) ? allSkills : (allSkills.items || [])
```

---

## 验证步骤

1. 启动服务：
   ```bash
   cd frontend && npm run dev
   ```

2. 登录 admin 页面（admin / Admin@123）

3. 测试功能：
   - 左侧：选择一个或多个技能（复选框应正常工作）
   - 右侧：选择一个或多个分类（复选框应正常工作）
   - 点击"绑定分类"按钮，确认对话框弹出
   - 确认后，操作成功消息显示
   - 刷新后分类关联正确保存

4. 测试边界情况：
   - 不选择技能时，按钮应禁用
   - 不选择分类时，按钮应禁用
   - 解绑功能同样应正常工作
