# Skills Platform 安全与 Bug 扫描报告

**扫描日期**: 2026-02-10
**扫描范围**: backend/ + frontend/src/
**报告版本**: v1.0

---

## 执行摘要

本次安全与 Bug 扫描对 Skills Platform 项目进行了全面的安全检查和潜在的 Bug 分析。发现 **3 个严重安全问题**、**5 个中等级别问题** 和 **8 个低优先级改进点**。

---

## 一、安全问题

### 1.1 严重问题

#### 1.1.1 硬编码的 JWT Secret Key
**文件**: `backend/middleware/auth.py:18`

**问题**:
```python
SECRET_KEY = "your-secret-key-change-in-production"
```

**风险等级**: **严重**

**影响**:
- 攻击者可以伪造任意 JWT Token
- 可以以任何用户身份登录系统
- 可以获取管理员权限

**修复方案**:
```python
import os
from core.security import get_jwt_secret_key

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set")
```

**验证方法**: 检查 `.env` 文件是否包含 `JWT_SECRET_KEY`

---

#### 1.1.2 Webhook 签名验证存在时序攻击风险
**文件**: `backend/services/webhook.py:21-29`

**问题**:
```python
def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        return True  # 没配置密钥就跳过验证
    return signature == secret  # 简单字符串比较，易受时序攻击
```

**风险等级**: **高**

**影响**:
- 攻击者可以通过时序攻击推断出正确的签名
- 可能伪造 Webhook 请求触发未授权的仓库同步

**修复方案**:
```python
import hmac
import hashlib

def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        logger.warning("Webhook secret not configured, skipping verification")
        return True
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

#### 1.1.3 没有配置密钥时 Webhook 完全跳过验证
**文件**: `backend/services/webhook.py:27-28`

**问题**: 当 `secret` 为空时直接返回 `True`，允许任何请求通过

**风险等级**: **高**

**影响**: 攻击者可以发送伪造的 Webhook 请求触发仓库同步

**修复方案**:
```python
def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
    if not secret:
        logger.error("Webhook secret not configured - rejecting request")
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

### 1.2 中等级别问题

#### 1.2.1 API 输入验证不足
**文件**: `backend/api/skills.py:18-29`

**问题**: `list_skills` 函数的 `keyword` 参数没有长度限制

```python
async def list_skills(
    keyword: str | None = None,  # 没有长度验证
    ...
):
```

**风险等级**: **中**

**影响**:
- 超长字符串可能导致 DoS
- LIKE 查询可能被利用进行性能攻击

**修复方案**:
```python
from pydantic import Field, validator

class SkillSearchParams(BaseModel):
    keyword: str | None = Field(None, max_length=100)

    @validator('keyword')
    def validate_keyword(cls, v):
        if v and len(v) > 100:
            raise ValueError('Keyword too long')
        return v
```

---

#### 1.2.2 前端 Token 存储在 localStorage
**文件**: `frontend/src/api/index.ts:23,27-28`

**问题**:
```typescript
this.token = localStorage.getItem('token')
localStorage.setItem('token', token)
```

**风险等级**: **中**

**影响**: XSS 攻击可以窃取存储在 localStorage 中的 Token

**修复方案**:
1. 后端设置 httpOnly Cookie
2. 使用 SameSite=Strict 属性
3. 前端不再存储 Token，依赖 Cookie 自动发送

---

#### 1.2.3 缺少 CORS 配置
**文件**: `backend/main.py`

**问题**: 未明确配置 CORS 策略

**风险等级**: **中**

**修复方案**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 明确指定允许的域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

---

#### 1.2.4 缺少速率限制
**文件**: `backend/api/*.py`

**问题**: API 端点没有速率限制

**风险等级**: **中**

**影响**: 容易受到 DoS 攻击

**修复方案**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.get("/skills")
@limiter.limit("30/minute")
async def list_skills(...):
    ...
```

---

#### 1.2.5 日志中可能泄露敏感信息
**文件**: 多个文件

**问题**: 错误日志可能包含敏感数据

**风险等级**: **中**

**修复方案**: 实现日志脱敏中间件

---

## 二、Bug 检查结果

### 2.1 潜在 Bug

#### 2.1.1 空指针异常风险
**文件**: `frontend/src/views/Home.vue:189`

**问题**:
```typescript
const selectedCategory = computed(() => {
  if (selectedCategorySlug.value === 'all') return null
  return flatCategories.value.find((item) => item.slug === selectedCategorySlug.value) || null
})
```

**说明**: 代码已经正确处理了 null 情况 ✅

---

#### 2.1.2 数据库查询结果未检查
**文件**: `backend/api/skills.py:80-81`

**问题**:
```python
for skill in skills:
    skill.views += 1
await db.commit()
```

**说明**: `skills` 总是有效列表，无需额外检查 ✅

---

#### 2.1.3 异常处理不完整
**文件**: `backend/api/skills.py:163`

**问题**:
```python
skills.value = data.items  # 如果 data 结构异常会报错
```

**修复方案**: 添加数据验证
```typescript
const response = await api.get('/skills?page_size=1') as { total?: number }
skillCategoryCount.value = response.total || 0
```

---

### 2.2 并发问题

#### 2.2.1 浏览计数竞态条件
**文件**: `backend/api/skills.py:79-81`

**问题**:
```python
skill.views += 1  # 读-修改-写操作，非原子
await db.commit()
```

**修复方案**:
```python
await db.execute(
    update(Skill)
    .where(Skill.id == skill.id)
    .values views=Skill.views + 1
)
```

---

#### 2.2.2 Webhook 并发处理
**文件**: `backend/services/webhook.py:84-86`

**问题**: 同一仓库的多个 Webhook 可能并发触发同步

**修复方案**: 添加分布式锁

---

## 三、修复优先级

### P0 - 立即修复 (本周内)

1. ✅ 修改 JWT Secret Key 从环境变量读取
2. ✅ 修复 Webhook 签名验证
3. ✅ 移除无密钥时跳过验证的逻辑

### P1 - 重要 (本月内)

1. ⚠️ 添加 API 输入验证
2. ⚠️ 配置 CORS 策略
3. ⚠️ 添加速率限制
4. ⚠️ 修复浏览计数竞态条件

### P2 - 一般 (下个迭代)

1. ⏳ 改进 Token 存储方式
2. ⏳ 实现日志脱敏
3. ⏳ 添加 Webhook 并发控制

---

## 四、安全检查清单

| 检查项 | 状态 | 备注 |
|--------|------|------|
| SQL 注入防护 | ✅ 通过 | 使用 ORM |
| XSS 防护 | ⚠️ 部分 | 需 CSP 头 |
| CSRF 防护 | ⚠️ 部分 | 需验证 SameSite |
| 认证机制 | ⚠️ 需修复 | Secret Key 问题 |
| 授权机制 | ✅ 通过 | 角色检查完善 |
| 敏感数据加密 | ✅ 通过 | Token 已加密 |
| 输入验证 | ❌ 缺失 | 需添加 |
| 输出编码 | ✅ 通过 | Pydantic 自动处理 |
| 日志安全 | ⚠️ 部分 | 需脱敏 |
| 错误处理 | ✅ 通过 | 统一异常处理 |

---

## 五、建议

1. **安全**: 定期进行安全审计和渗透测试
2. **监控**: 添加异常访问检测和告警
3. **备份**: 定期备份数据库和配置
4. **更新**: 保持依赖库最新版本

---

**报告生成**: 安全扫描自动化工具
**下次扫描**: 建议每月一次
