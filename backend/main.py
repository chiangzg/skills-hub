"""
Skills Platform - FastAPI 主入口
"""
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core import logger
from core.error_handler import (
    skills_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from core.exceptions import SkillsException
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from middleware.security import SecurityHeadersMiddleware, LoggingMiddleware, RateLimitMiddleware
from database import init_db

# API 路由
from api import auth, users, repositories, categories, skills, webhooks, sync, public_categories


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("Starting Skills Platform...")

    # 初始化数据库连接
    db_ok = await init_db()
    if not db_ok:
        logger.warning("Database connection failed, continuing anyway...")

    yield

    # 关闭时
    logger.info("Shutting down Skills Platform...")
    from database import close_db
    await close_db()


# 创建 FastAPI 应用
app = FastAPI(
    title="Skills Platform",
    description="内部技能管理发现平台",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS 中间件 - 从环境变量读取允许的来源
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 自定义中间件
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# 异常处理器
app.add_exception_handler(SkillsException, skills_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# 注册 API 路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(public_categories.router)  # 公开分类 API（无需认证）
app.include_router(repositories.router)
app.include_router(categories.router)  # 管理员分类 API（需要认证）
app.include_router(skills.router)
app.include_router(webhooks.router)
app.include_router(sync.router)


# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    from database import engine
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": f"disconnected: {str(e)}"
        }


# SPA 路由回退：对于非 API 请求，返回 index.html
@app.get("/admin")
@app.get("/admin/{full_path:path}")
@app.get("/categories")
@app.get("/categories/{full_path:path}")
@app.get("/skills/{full_path:path}")
@app.get("/login")
async def spa_fallback():
    """SPA 路由回退：返回 index.html"""
    return FileResponse("./frontend/dist/index.html")


# 挂载前端静态文件（生产环境）
# 必须在所有其他路由之后挂载，否则会覆盖 API 路由
try:
    app.mount("/", StaticFiles(directory="./frontend/dist", html=True), name="frontend")
except Exception as e:
    logger.info(f"Frontend static files not found, running in API-only mode: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
