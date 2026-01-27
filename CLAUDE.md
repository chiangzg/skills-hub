# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Skills Platform is an internal skill discovery and management platform. It automatically discovers and syncs "Skills" from GitHub/GitLab repositories, where a Skill is defined by a `SKILL.md` file in any directory. The platform features a CLI-style terminal UI and supports webhook-based auto-sync on GitLab push events.

**Tech Stack:**
- Backend: FastAPI 0.128.0 + Python 3.13 + MySQL 8.0
- Frontend: Vue 3.5.25 + TypeScript + Vite
- Deployment: Docker (single image with MySQL)

## Common Commands

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with database credentials and JWT_SECRET_KEY

# Run development server (auto-reload)
python main.py
# Server runs on http://localhost:8000
# API docs: http://localhost:8000/api/docs
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Run dev server (proxies /api and /webhooks to backend)
npm run dev
# Server runs on http://localhost:5173

# Build for production
npm run build
```

### Database
```bash
# Initialize database (run once)
mysql -u root -p < backend/schema.sql

# Default admin credentials: admin / Admin@123
```

### Docker Deployment
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f skills

# Stop services
docker-compose down
```

## Architecture

### Backend Structure

**Core Layers:**
- `api/` - FastAPI route handlers (thin, delegate to services)
- `services/` - Business logic layer
  - `scanner.py` - `SkillScanner.sync_repository()` orchestrates repo download, skill discovery, and DB sync
  - `parser.py` - `SkillParser` parses `SKILL.md` YAML front matter (name, description, tags)
  - `github.py` / `gitlab.py` - Git service clients for repo download
  - `webhook.py` - GitLab push event handler
- `models/` - SQLAlchemy ORM models (User, Repository, Skill, Category, WebhookLog)
- `schemas/` - Pydantic validation schemas
- `middleware/` - `auth.py` (JWT auth, `get_current_user()`, `require_admin()`), security headers, rate limiting
- `core/` - `security.py` (encryption for tokens), `exceptions.py` (custom exception classes), logger

**Database Pattern:**
- Async SQLAlchemy with `aiomysql`
- `get_db()` dependency injection provides `AsyncSession`
- Models have `to_dict()` method for serialization
- Access tokens and webhook secrets are encrypted at rest using `core.security.encryption`

**Skill Discovery Flow:**
1. Repository added via API (GitHub or GitLab, with optional access token)
2. `/api/admin/repositories/{id}/sync` triggers `SkillScanner.sync_repository()`
3. Repo downloaded to temp dir, walked recursively for `SKILL.md` files
4. Each `SKILL.md` parsed for YAML front matter metadata
5. Skills synced to DB (add/update/remove based on directory path)
6. GitLab webhooks can trigger auto-sync via `/webhooks/gitlab/{repo_id}`

### Frontend Structure

- `src/views/` - Page components (Home, Category, Skill, Login, admin/Dashboard)
- `src/components/admin/` - Admin panels (RepositoryPanel, CategoryPanel, UserPanel)
- `src/router/index.ts` - Vue Router with auth guards (`requiresAuth`, `requiresAdmin`)
- `src/api/index.ts` - HTTP client (uses `fetch`, stores token in localStorage)

**Auth Flow:**
- Login stores JWT in `localStorage`
- Router guard checks `token` and `userRole` for protected routes
- API calls include `Authorization: Bearer <token>` header

### Key Configuration Files

- `backend/database.py` - SQLAlchemy async engine config, connection pooling
- `backend/main.py` - App lifespan, middleware registration, route inclusion
- `docker-compose.yml` - Single service + MySQL with health checks
- `frontend/vite.config.ts` - Dev server with backend proxy

## Important Notes

- JWT_SECRET_KEY and ENCRYPTION_KEY must be set in production
- Access tokens for private repositories are encrypted before storage
- GitLab webhook URL format: `/webhooks/gitlab/{repo_id}` with shared secret
- SKILL.md format: YAML front matter (`---\nname: ...\n---`) followed by content
- MySQL schema initialization uses `schema.sql` in docker volume mount
