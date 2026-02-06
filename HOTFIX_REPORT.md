# Skills Platform - Hotfix Report

**测试日期**: 2026-02-06
**测试人员**: Claude Code
**测试环境**: Docker Compose (本地)

---

## 一、测试概述

本次测试对 Skills Platform 进行了全面的功能测试，包括：
1. 前台浏览功能（首页、分类浏览、技能详情）
2. 后台管理功能（登录、仓库管理、分类管理、用户管理）
3. 仓库同步功能（GitHub/GitLab 仓库同步）

**测试账号**: admin / Admin@123

---

## 二、发现的问题

### 1. 【严重】Access Token 解密失败导致同步失败

**问题描述**:
- GitLab 仓库同步返回 `401 Unauthorized` 错误
- 错误信息：`Failed to download tarball: 401`

**根本原因**:
1. `backend/services/scanner.py` 中直接使用了 `repo.access_token`（加密后的值），没有先解密
2. 更严重的是：`ENCRYPTION_KEY` 环境变量未设置，导致每次重启容器都会生成新的加密密钥
3. 之前用旧密钥加密的 token 无法用新密钥解密，导致认证失败

**影响范围**:
- 所有需要 access_token 的私有仓库同步
- 所有已配置的 GitLab/GitHub 私有仓库

**修复方案**:
1. 修改 `backend/services/scanner.py`：在传递 token 前先进行解密
2. 创建 `.env` 文件，设置固定的 `ENCRYPTION_KEY`
3. 改进错误处理，当解密失败时给出明确的错误提示

**修复文件**:
- `backend/services/scanner.py` (第 158-180 行)
- `backend/services/gitlab.py` (第 81-100 行，第 136-150 行)
- `.env` (新建文件)

---

### 2. 【中等】前端 API 调用路径错误

**问题描述**:
- 首页访问时控制台报错，无法获取统计数据
- 管理后台数据统计显示异常

**根本原因**:
前端调用的 API 路径与后端实际路径不匹配：

| 前端调用 | 实际后端路径 | 状态 |
|---------|-------------|------|
| `/api/repositories` | `/api/admin/repositories` | 需要认证 |
| `/api/categories` | `/api/admin/categories` (后台) 或 `/api/categories` (前台) | 混淆 |

**影响范围**:
- `frontend/src/views/Home.vue` - 首页统计
- `frontend/src/views/admin/Dashboard.vue` - 管理后台统计

**修复方案**:
1. 修改 `Home.vue`：移除对 `/repositories` 的调用（前台不应显示仓库信息）
2. 修改 `Dashboard.vue`：使用正确的 `/admin/repositories` 路径

**修复文件**:
- `frontend/src/views/Home.vue` (第 98-118 行)
- `frontend/src/views/admin/Dashboard.vue` (第 136-150 行)

---

### 3. 【低】代码逻辑问题（gitlab.py）

**问题描述**:
`gitlab.py` 中存在不可达代码

**根本原因**:
在第 88 行调用 `return await self._download_tarball(...)` 后，第 91 行的 `raise` 语句永远不会执行

**修复方案**:
移除不可达代码，将错误处理移到 `_download_tarball` 方法内部

**修复文件**:
- `backend/services/gitlab.py` (第 81-100 行)

---

## 三、修复详情

### 后端修复

#### 1. `backend/services/scanner.py`

**修改前**:
```python
async def _download_repo(self, repo: Repository, temp_dir: Path | None = None) -> Path:
    try:
        if repo.type == RepositoryType.GITHUB:
            return await github_service.download_repo(
                # ... 省略
                access_token=repo.access_token,  # 直接使用加密的 token
            )
    except Exception as e:
        logger.error(f"Failed to download repository {repo.full_name}: {e}")
        raise ExternalServiceError(repo.type.value, str(e))
```

**修改后**:
```python
async def _download_repo(self, repo: Repository, temp_dir: Path | None = None) -> Path:
    try:
        # 解密 access_token
        decrypted_token = None
        if repo.access_token:
            try:
                decrypted_token = encryption.decrypt(repo.access_token)
                logger.info(f"Successfully decrypted access token for {repo.full_name}")
            except Exception as e:
                logger.error(f"Failed to decrypt access token for {repo.full_name}: {e}")
                raise ExternalServiceError(
                    repo.type.value,
                    "Access token decryption failed. The ENCRYPTION_KEY may have changed. "
                    "Please re-enter the access token for this repository."
                )

        if repo.type == RepositoryType.GITHUB:
            return await github_service.download_repo(
                # ... 使用 decrypted_token
            )
    except ExternalServiceError:
        raise
    except Exception as e:
        logger.error(f"Failed to download repository {repo.full_name}: {e}")
        raise ExternalServiceError(repo.type.value, str(e))
```

#### 2. `backend/services/gitlab.py`

**修改前**:
```python
except httpx.HTTPStatusError as e:
    logger.warning(f"ZIP download failed ({e.response.status_code}), trying tar.gz")
    return await self._download_tarball(owner, name, branch, access_token, temp_dir)

    # 以下代码永远不会执行
    raise ExternalServiceError("GitLab", f"Failed to download: {e.response.status_code}")
```

**修改后**:
```python
except httpx.HTTPStatusError as e:
    logger.warning(f"ZIP download failed ({e.response.status_code}), trying tar.gz")
    try:
        return await self._download_tarball(owner, name, branch, access_token, temp_dir)
    except Exception:
        error_msg = f"Failed to download: HTTP {e.response.status_code}"
        if not access_token and e.response.status_code == 401:
            error_msg += ". This may be a private repository. Please provide an access token."
        raise ExternalServiceError("GitLab", error_msg)
```

#### 3. 新建 `.env` 文件

创建项目根目录下的 `.env` 文件，设置固定的加密密钥：

```env
# JWT 密钥
JWT_SECRET_KEY=skills-jwt-secret-key-2024-production

# 数据库加密密钥（固定值，避免每次重启生成新密钥）
ENCRYPTION_KEY=Z7vW9yX4kL2mN8pQ5sT6wR3jH7fG1cV9aB5nD2zM8xK6yP4oJ3q=

# 其他配置...
```

---

### 前端修复

#### 1. `frontend/src/views/Home.vue`

**修改前**:
```javascript
const [skillsRes, reposRes] = await Promise.all([
  api.get('/skills?page_size=1'),
  api.get('/repositories')  // 错误：此端点需要认证
])

stats.value = {
  total_skills: skillsRes.total || 0,
  total_categories: categoryData.length,
  total_repositories: Array.isArray(reposRes) ? reposRes.length : 0
}
```

**修改后**:
```javascript
const [skillsRes] = await Promise.all([
  api.get('/skills?page_size=1')
  // 移除 repositories 调用
])

stats.value = {
  total_skills: skillsRes.total || 0,
  total_categories: categoryData.length,
  total_repositories: 0  // 前台不显示仓库数量
}
```

#### 2. `frontend/src/views/admin/Dashboard.vue`

**修改前**:
```javascript
const [repos, categories, users] = await Promise.all([
  api.get('/repositories').catch(() => []),  // 错误路径
  api.get('/categories').catch(() => []),    // 错误路径
  // ...
])
```

**修改后**:
```javascript
const [repos, categories, users] = await Promise.all([
  api.get('/admin/repositories').catch(() => []),  // 正确路径
  api.get('/admin/categories').catch(() => []),    // 正确路径
  // ...
])
```

---

## 四、用户操作指引

由于 `ENCRYPTION_KEY` 已更改，之前存储的 access_token 将无法解密。用户需要**重新配置仓库的访问令牌**：

1. 登录管理后台
2. 进入「仓库管理」
3. 对每个需要访问令牌的仓库：
   - 点击「编辑」
   - 重新填写 access_token
   - 保存
4. 重新执行同步操作

---

## 五、测试验证

### 测试用例 1：公开 API 访问（无需认证）

```bash
# 健康检查
curl http://localhost:8000/api/health
# 预期: {"status":"healthy","database":"connected"}

# 获取分类树
curl http://localhost:8000/api/categories/tree
# 预期: 返回分类树 JSON

# 获取技能列表
curl http://localhost:8000/api/skills?page_size=10
# 预期: 返回技能列表 JSON
```

### 测试用例 2：管理员 API 访问（需要认证）

```bash
# 登录获取 token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}' \
  | jq -r '.access_token')

# 获取仓库列表
curl http://localhost:8000/api/admin/repositories \
  -H "Authorization: Bearer $TOKEN"
# 预期: 返回仓库列表 JSON

# 同步仓库
curl -X POST http://localhost:8000/api/admin/repositories/1/sync \
  -H "Authorization: Bearer $TOKEN"
# 预期: 如果 token 正确配置，返回同步结果；如果 token 解密失败，返回明确错误信息
```

---

## 六、建议

1. **环境变量管理**: 建议将 `.env` 文件添加到 `.gitignore`，并在部署时使用正确的环境变量

2. **密钥轮换**: 如果未来需要更换 `ENCRYPTION_KEY`，需要：
   - 提前通知用户重新配置 access_token
   - 或者实现密钥迁移机制

3. **错误处理改进**: 建议在后续版本中添加更友好的错误提示，帮助用户快速定位问题

4. **前端路由**: 考虑在开发模式下使用代理，避免 CORS 问题

---

## 七、总结

本次 hotfix 修复了 **3 个问题**，包括 1 个严重问题（token 解密失败）、1 个中等问题（API 路径错误）和 1 个低等问题（代码逻辑问题）。

所有修复已经应用到代码仓库，用户需要：
1. 重新构建 Docker 镜像：`docker compose up -d --build`
2. 重新配置仓库的 access_token
3. 测试同步功能

**测试状态**: 修复已就绪，等待用户重新配置 token 后验证
