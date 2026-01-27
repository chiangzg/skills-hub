"""
同步 API
"""
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import User, Repository
from schemas.repository import SyncResponse
from middleware.auth import get_current_user
from services.scanner import SkillScanner
from core import NotFoundError, logger

router = APIRouter(prefix="/api/admin/sync", tags=["Sync"])


@router.post("/{repo_id}", response_model=SyncResponse)
async def sync_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动同步单个仓库"""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise NotFoundError("Repository", repo_id)

    scanner = SkillScanner(db)
    result = await scanner.sync_repository(repo)

    return SyncResponse(**result)


@router.post("/all", response_model=dict)
async def sync_all_repositories(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """同步所有启用的仓库"""
    from sqlalchemy import select

    result = await db.execute(
        select(Repository).where(Repository.enabled == True)
    )
    repos = result.scalars().all()

    results = []
    scanner = SkillScanner(db)

    for repo in repos:
        try:
            result = await scanner.sync_repository(repo)
            results.append({
                "repository": repo.full_name,
                "status": "success",
                **result
            })
        except Exception as e:
            logger.error(f"Failed to sync {repo.full_name}: {e}")
            results.append({
                "repository": repo.full_name,
                "status": "failed",
                "error": str(e)
            })

    return {
        "total": len(repos),
        "results": results
    }


@router.get("/status", response_model=dict)
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取同步状态"""
    from sqlalchemy import select, func

    # 统计各状态的仓库数
    result = await db.execute(
        select(
            func.count().label("total"),
            func.sum(func.case((Repository.last_sync_at.isnot(None), 1), else_=0)).label("synced")
        ).select_from(Repository)
    )
    row = result.one()

    # 获取最近同步的仓库
    recent_result = await db.execute(
        select(Repository)
        .where(Repository.last_sync_at.isnot(None))
        .order_by(Repository.last_sync_at.desc())
        .limit(5)
    )
    recent = recent_result.scalars().all()

    return {
        "total_repositories": row.total or 0,
        "synced_repositories": row.synced or 0,
        "recently_synced": [
            {
                "id": r.id,
                "name": r.full_name,
                "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None
            }
            for r in recent
        ]
    }
