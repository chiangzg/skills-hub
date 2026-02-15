"""
公开 API - Skill 下载接口
无需认证，供 CLI 工具使用
"""
from fastapi import APIRouter, HTTPException, Path as PathParam, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database import get_db
from models import Skill, Repository, CacheConfig
from services.cache import CacheService
from core import logger, NotFoundError

router = APIRouter(prefix="/api/public", tags=["Public"])


@router.get("/skills/{skill_identifier}/download")
async def download_skill(
    skill_identifier: str = PathParam(..., description="Skill ID 或 Skill 名称"),
    db: AsyncSession = Depends(get_db)
):
    """
    下载单个 Skill 的所有文件
    
    返回 JSON 格式，包含 Skill 的所有文件内容
    """
    # 尝试通过 ID 或名称查找 Skill
    skill = None
    
    # 尝试作为 ID 查找
    if skill_identifier.isdigit():
        skill = await db.get(Skill, int(skill_identifier))
    
    # 如果没找到，尝试通过名称查找
    if not skill:
        result = await db.execute(
            select(Skill).where(Skill.name == skill_identifier)
        )
        skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_identifier}")
    
    # 获取关联的仓库信息
    if skill.repository_id:
        repo = await db.get(Repository, skill.repository_id)
    else:
        repo = None
    
    # 初始化缓存服务
    cache_service = CacheService(db)
    await cache_service.initialize()
    
    # 获取 Skill 文件
    files = await cache_service.get_skill_files(skill)
    
    if not files:
        raise HTTPException(
            status_code=404, 
            detail=f"Skill files not found in cache. Please sync the repository first."
        )
    
    # 计算总大小
    total_size = sum(f["size"] for f in files)
    
    # 构建响应
    response = {
        "name": skill.name,
        "description": skill.description,
        "version": repo.cache_version[:12] if repo and repo.cache_version else None,
        "repository": {
            "type": repo.type.value if repo else None,
            "owner": repo.owner if repo else None,
            "name": repo.name if repo else None,
            "branch": repo.branch if repo else None,
        } if repo else None,
        "files": files,
        "total_files": len(files),
        "total_size": total_size,
        "downloaded_at": datetime.utcnow().isoformat()
    }
    
    logger.info(f"Skill downloaded: {skill.name}, files: {len(files)}, size: {total_size}")
    
    return JSONResponse(content=response)


@router.get("/skills/{skill_identifier}/cli-command")
async def get_cli_command(
    skill_identifier: str = PathParam(..., description="Skill ID 或 Skill 名称"),
    db: AsyncSession = Depends(get_db)
):
    """
    获取 CLI 下载命令
    
    返回用于复制到剪贴板的命令
    """
    # 尝试通过 ID 或名称查找 Skill
    skill = None
    
    if skill_identifier.isdigit():
        skill = await db.get(Skill, int(skill_identifier))
    
    if not skill:
        result = await db.execute(
            select(Skill).where(Skill.name == skill_identifier)
        )
        skill = result.scalar_one_or_none()
    
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill not found: {skill_identifier}")
    
    # 获取 Hub URL
    cache_service = CacheService(db)
    await cache_service.initialize()
    hub_url = cache_service.get_config("skill_hub_url", "http://localhost:8000")
    
    return {
        "command": f"skill download {skill.name}",
        "skill_name": skill.name,
        "api_endpoint": f"{hub_url}/api/public/skills/{skill.name}/download"
    }


@router.get("/config")
async def get_public_config(db: AsyncSession = Depends(get_db)):
    """
    获取公开配置信息
    
    供 CLI 工具获取服务器配置
    """
    cache_service = CacheService(db)
    await cache_service.initialize()
    
    return {
        "skill_hub_url": cache_service.get_config("skill_hub_url", "http://localhost:8000"),
        "skill_download_dir": cache_service.get_config("skill_download_dir", "./skills"),
        "max_file_size_mb": int(cache_service.get_config("max_file_size_mb", "10")),
        "max_skill_size_mb": int(cache_service.get_config("max_skill_size_mb", "50"))
    }


@router.get("/cache/stats")
async def get_cache_stats(db: AsyncSession = Depends(get_db)):
    """
    获取缓存统计信息
    """
    cache_service = CacheService(db)
    await cache_service.initialize()
    
    return await cache_service.get_cache_stats()
