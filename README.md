# Skills Platform

内部技能管理发现平台

## 功能特性

- 🔍 **技能发现**：从 GitHub/GitLab 仓库自动发现和同步 Skills
- 📂 **分类管理**：多级分类组织技能
- 🔐 **用户认证**：基于 JWT 的用户认证和权限控制
- 🔔 **Webhook**：GitLab Push 事件自动触发同步
- 💻 **CLI 风格**：仿终端命令行界面

## 技术栈

- **后端**：FastAPI 0.128.0 + Python 3.13
- **前端**：Vue 3.5.25 + TypeScript
- **数据库**：MySQL 8.0+
- **部署**：Docker 单服务部署

## 目录结构

```
skills-hub-cc/
├── backend/                 # FastAPI 后端
│   ├── api/                 # API 路由
│   ├── models/              # 数据库模型
│   ├── schemas/             # 数据验证
│   ├── services/            # 业务服务
│   ├── middleware/          # 中间件
│   ├── core/                # 核心模块
│   ├── main.py              # 应用入口
│   ├── database.py          # 数据库配置
│   ├── requirements.txt     # Python 依赖
│   └── schema.sql           # 数据库初始化
├── frontend/                # Vue 3 前端
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # UI 组件
│   │   ├── api/             # API 客户端
│   │   └── router/          # 路由配置
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml        # Docker 编排
├── Dockerfile               # 服务镜像
└── README.md
```

## 快速开始

### 1. 数据库初始化

```bash
# 创建数据库并初始化
mysql -u root -p < backend/schema.sql
```

### 2. 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接和密钥

# 启动服务
python main.py
```

后端将在 http://localhost:8000 启动

API 文档：http://localhost:8000/api/docs

### 3. 前端启动（开发模式）

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 http://localhost:5173 启动

### 4. Docker 部署

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f skills

# 停止服务
docker-compose down
```

## 默认账号

- **用户名**：`admin`
- **密码**：`Admin@123`

> ⚠️ 首次部署后请立即修改默认密码！

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | MySQL 连接字符串 | `mysql+aiomysql://skills:skills_password@localhost:3306/skills` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | `your-jwt-secret-key-change-in-production` |
| `ENCRYPTION_KEY` | 敏感数据加密密钥 | 自动生成 |

## API 接口

### 认证 API
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户
- `POST /api/auth/change-password` - 修改密码

### 仓库管理 API
- `GET /api/admin/repositories` - 仓库列表
- `POST /api/admin/repositories` - 添加仓库
- `PUT /api/admin/repositories/{id}` - 更新仓库
- `DELETE /api/admin/repositories/{id}` - 删除仓库
- `POST /api/admin/repositories/{id}/sync` - 手动同步

### 分类管理 API
- `GET /api/admin/categories/tree` - 分类树
- `POST /api/admin/categories` - 创建分类
- `PUT /api/admin/categories/{id}` - 更新分类
- `DELETE /api/admin/categories/{id}` - 删除分类

### Skill API
- `GET /api/skills` - 搜索/浏览 Skills
- `GET /api/skills/{id}` - Skill 详情
- `GET /api/categories/{slug}/skills` - 分类下的 Skills

### Webhook API
- `POST /webhooks/gitlab/{repo_id}` - GitLab Webhook 接收

## GitLab Webhook 配置

1. 在 GitLab 项目设置中添加 Webhook
2. URL：`http://your-server/webhooks/gitlab/{repo_id}`
3. Secret Token：与仓库配置的 webhook_secret 一致
4. 触发事件：Push events
5. 保存后，Push 代码将自动触发同步

## Skill 识别规则

在仓库的任意目录下创建 `SKILL.md` 文件：

```markdown
---
name: "技能名称"
description: "技能描述"
tags: ["tag1", "tag2"]
---

这里是详细的技能说明...
```

## License

MIT
