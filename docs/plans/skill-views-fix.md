# Skill 热度更新逻辑调整计划

## Context

当前热度（views）更新逻辑存在问题：每次调用 `/api/skills` 列表接口时，后端会自动将返回的所有 skills 的 views +1。这意味着：
- 用户每次翻页都会增加当前页所有技能的浏览量
- 切换筛选条件（分类、搜索）也会增加热度
- 这不是真正反映"用户对该技能感兴趣"的行为

**预期行为：** 只有当用户真正查看技能详情时才增加热度。

---

## 实现方案

### 修改文件

**后端修改：**
- `backend/api/skills.py` - 移除列表接口中的 views 自动更新逻辑

### 具体改动

**backend/api/skills.py (第 78-81 行)**

删除以下代码：
```python
# 增加浏览计数
for skill in skills:
    skill.views += 1
await db.commit()
```

**保留详情页的热度更新：**
- `GET /api/skills/{skill_id}` 接口（第 115-117 行）保持不变
  - 用户点击进入详情页时会正确增加热度

### 验证步骤

1. 启动服务：`docker compose up`
2. 测试场景：
   - 在首页翻页、切换筛选条件 -> 数据库 views 不应增加
   - 点击技能进入详情页 -> 该 skill 的 views 应 +1
3. 检查数据库：`SELECT id, name, views FROM skills ORDER BY views DESC LIMIT 10;`
