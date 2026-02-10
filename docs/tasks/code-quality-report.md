# Skills Platform 代码质量扫描报告

**扫描日期**: 2026-02-10
**扫描范围**: backend/ + frontend/src/
**报告版本**: v1.0

---

## 执行摘要

本次代码质量扫描对 Skills Platform 项目的后端 (Python/FastAPI) 和前端 (Vue/TypeScript) 代码进行了全面分析。整体代码质量良好，但发现了一些需要优化的地方。

### 总体评分

| 模块 | 代码质量 | 安全性 | 可维护性 |
|------|----------|--------|----------|
| 后端 (backend/) | B+ | A- | B |
| 前端 (frontend/src/) | B | B+ | B+ |

---

## 一、后端代码分析 (Python/FastAPI)

### 1.1 高优先级问题

#### 1.1.1 硬编码的 JWT Secret Key
**文件**: `backend/middleware/auth.py:18`
```python
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境从环境变量读取
```
**严重程度**: **严重**
**风险**: 生产环境使用默认密钥会导致 JWT Token 可被破解
**修复建议**:
```python
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
```

#### 1.1.2 SQL 注入风险（实际无风险，但需注意）
**文件**: `backend/api/skills.py:44-47`
```python
query = query.where(
    or_(
        Skill.name.like(f"%{keyword}%"),
        Skill.description.like(f"%{keyword}%")
    )
)
```
**严重程度**: **低**
**说明**: 使用 SQLAlchemy ORM，参数会被正确转义，但 LIKE 查询中的 `%keyword%` 可能存在性能问题
**修复建议**: 考虑使用全文搜索引擎（如 Elasticsearch）或 MySQL FULLTEXT 索引

#### 1.1.3 Webhook 签名验证不足
**文件**: `backend/services/webhook.py:21-29`
```python
def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return True  # 如果没配置密钥，跳过验证
    return signature == secret
```
**严重程度**: **高**
**风险**: 简单字符串比较，不防止时序攻击
**修复建议**:
```python
import hmac
def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return True
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### 1.2 中优先级问题

#### 1.2.1 过长函数
**文件**: `backend/services/scanner.py:70-156`
**函数**: `sync_repository`
**行数**: 87 行
**修复建议**: 拆分为 `_process_skill`, `_delete_removed_skills`, `_update_repository_stats` 等子函数

**文件**: `backend/api/repositories.py:93-167`
**函数**: `create_repository`
**行数**: 75 行
**修复建议**: 提取 GitLab URL 解析和验证逻辑到单独函数

#### 1.2.2 重复代码
**文件**: `backend/api/skills.py:79-81` 和 `115-117`
```python
# 增加浏览计数
skill.views += 1
await db.commit()
```
**修复建议**: 创建通用函数 `increment_skill_views(skill_id, db)`

#### 1.2.3 未使用的导入
**文件**: `backend/services/webhook.py:6`
```python
from fastapi import BackgroundTasks  # 未使用
```
**修复建议**: 删除未使用的导入

### 1.3 低优先级问题

#### 1.3.1 类型注解缺失
**文件**: `backend/services/scanner.py:27-68`
**问题**: 部分函数参数缺少类型注解
**修复建议**: 为所有函数参数添加类型注解

#### 1.3.2 过多的参数
**文件**: `backend/api/skills.py:18-29`
**函数**: `list_skills`
**参数数量**: 8 个
**修复建议**: 使用 Pydantic 模型封装查询参数

---

## 二、前端代码分析 (Vue/TypeScript)

### 2.1 高优先级问题

#### 2.1.1 localStorage 存储敏感信息
**文件**: `frontend/src/api/index.ts:23,27-28`
```typescript
this.token = localStorage.getItem('token')
localStorage.setItem('token', token)
```
**严重程度**: **中**
**风险**: XSS 攻击可窃取 Token
**修复建议**: 考虑使用 httpOnly Cookie 存储 Token

#### 2.1.2 any 类型使用过多
**文件**: `frontend/src/api/index.ts:72,114,142,163,196`
```typescript
async post<T>(endpoint: string, body?: any): Promise<T>
async create(data: any) { ... }
```
**严重程度**: **中**
**修复建议**: 定义具体的接口类型替代 `any`

### 2.2 中优先级问题

#### 2.2.1 过长组件
**文件**: `frontend/src/views/Home.vue`
**行数**: 700+ 行
**修复建议**: 拆分为多个子组件（如 `SkillRankTable`, `CategoryFilter`, `SearchBar` 等）

**文件**: `frontend/src/views/admin/Dashboard.vue`
**行数**: 507 行
**修复建议**: 提取 Tab 导航为独立组件

#### 2.2.2 重复的分类树构建逻辑
**文件**: `frontend/src/views/Home.vue:247-279`
**问题**: `buildCategoryTree` 函数在多个组件中重复
**状态**: ✅ 已通过 `CategorySidebar` 组件解决

#### 2.2.3 魔法数字
**文件**: `frontend/src/views/Home.vue:206`
```typescript
const pageSize = 20
```
**修复建议**: 提取为常量 `const DEFAULT_PAGE_SIZE = 20`

### 2.3 低优先级问题

#### 2.3.1 未使用的变量
**文件**: `frontend/src/views/Category.vue:95`
```typescript
const selectedCategory = ref<CategoryItem | null>(null)
```
**说明**: 实际已使用，但 TypeScript 推断可能有误

#### 2.3.2 console.log 残留
**文件**: `backend/services/webhook.py:94`
```python
logger.error(f"Webhook processing failed: {e}", exc_info=True)
```
**说明**: 已使用 logger，符合规范

---

## 三、安全问题汇总

### 3.1 认证与授权

| 问题 | 严重程度 | 状态 |
|------|----------|------|
| 硬编码 JWT Secret Key | 严重 | 需修复 |
| Token 存储在 localStorage | 中 | 建议改进 |
| Webhook 签名验证不足 | 高 | 需修复 |
| 密码加密存储 | ✅ 已实现 | - |

### 3.2 输入验证

| 检查项 | 状态 | 备注 |
|--------|------|------|
| SQL 注入防护 | ✅ 通过 | 使用 ORM |
| XSS 防护 | ⚠️ 部分 | 需 CSP 头 |
| 输入长度限制 | ❌ 缺失 | API 无验证 |
| 文件上传验证 | N/A | 当前无此功能 |

### 3.3 敏感数据处理

| 检查项 | 状态 | 备注 |
|--------|------|------|
| Access Token 加密 | ✅ 通过 | 使用 Fernet |
| Webhook Secret 加密 | ✅ 通过 | 使用 Fernet |
| 密码哈希 | ✅ 通过 | 使用 bcrypt |
| 日志脱敏 | ⚠️ 部分 | 建议增强 |

---

## 四、代码异味

### 4.1 后端

1. **深层嵌套**: `backend/api/repositories.py:100-133` (3层嵌套)
2. **长参数列表**: `backend/api/skills.py:list_skills` (8个参数)
3. **重复的异常处理模式**: 多处 `try-except` 块结构相似

### 4.2 前端

1. **大型组件**: 多个组件超过 300 行
2. **Props 穿透**: 部分 props 多层传递
3. **any 类型**: TypeScript 类型安全性不足

---

## 五、修复建议优先级

### P0 - 立即修复

1. 修改 JWT Secret Key 从环境变量读取
2. 修复 Webhook 签名验证

### P1 - 本周修复

1. 添加 API 输入验证和长度限制
2. 拆分过长函数和组件
3. 修复前端 `any` 类型问题

### P2 - 下个迭代

1. 添加 CSP 头增强 XSS 防护
2. 提取重复代码为工具函数
3. 完善日志脱敏

---

## 六、良好实践

1. ✅ 使用 SQLAlchemy ORM 防止 SQL 注入
2. ✅ 敏感数据加密存储
3. ✅ JWT 认证机制
4. ✅ 异步 API 处理
5. ✅ 统一的异常处理
6. ✅ 可复用的 CategorySidebar 组件

---

**报告生成**: 自动化扫描工具
**下次扫描**: 建议每月一次
