"""
仓库管理 API
"""
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Repository
from schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    WebhookConfig,
    SyncResponse
)
from middleware.auth import get_current_user
from services.scanner import SkillScanner
from core import NotFoundError, ConflictError, encryption
from core.security import generate_encryption_key

router = APIRouter(prefix="/api/admin/repositories", tags=["Repositories"])


@router.get("", response_model=list[RepositoryResponse])
async def list_repositories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库列表"""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.skills))
        .order_by(Repository.created_at.desc())
    )
    repos = result.scalars().all()

    # 为每个仓库统计 skill 数量
    responses = []
    for repo in repos:
        repo_dict = repo.to_dict()
        repo_dict["skill_count"] = len(repo.skills)
        responses.append(RepositoryResponse(**repo_dict))

    return responses


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repo_data: RepositoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """添加新仓库"""
    # 检查是否已存在
    result = await db.execute(
        select(Repository).where(
            Repository.owner == repo_data.owner,
            Repository.name == repo_data.name,
            Repository.branch == repo_data.branch
        )
    )
    if result.scalar_one_or_none():
        raise ConflictError(
            message="Repository already exists",
            resource="repository"
        )

    # 加密 access token
    encrypted_token = None
    if repo_data.access_token:
        encrypted_token = encryption.encrypt(repo_data.access_token)

    repo = Repository(
        type=repo_data.type,
        owner=repo_data.owner,
        name=repo_data.name,
        branch=repo_data.branch,
        gitlab_url=repo_data.gitlab_url,
        access_token=encrypted_token
    )

    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    return RepositoryResponse(**repo.to_dict())


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取仓库详情"""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.skills))
        .where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository", repo_id)

    repo_dict = repo.to_dict()
    repo_dict["skill_count"] = len(repo.skills)
    return RepositoryResponse(**repo_dict)


@router.put("/{repo_id}", response_model=RepositoryResponse)
async def update_repository(
    repo_id: int,
    repo_data: RepositoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """更新仓库配置"""
    result = await db.execute(
        select(Repository)
        .options(selectinload(Repository.skills))
        .where(Repository.id == repo_id)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise NotFoundError("Repository", repo_id)

    if repo_data.branch is not None:
        repo.branch = repo_data.branch
    if repo_data.enabled is not None:
        repo.enabled = repo_data.enabled

    # 加密新的 token
    if repo_data.access_token is not None:
        repo.access_token = encryption.encrypt(repo_data.access_token) if repo_data.access_token else None

    await db.commit()
    await db.refresh(repo)

    repo_dict = repo.to_dict()
    repo_dict["skill_count"] = len(repo.skills)
    return RepositoryResponse(**repo_dict)


@router.delete("/{repo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repo_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除仓库"""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise NotFoundError("Repository", repo_id)

    await db.delete(repo)
    await db.commit()


@router.post("/{repo_id}/sync", response_model=SyncResponse)
async def sync_repository(
    repo_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """手动同步仓库"""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise NotFoundError("Repository", repo_id)

    scanner = SkillScanner(db)
    result = await scanner.sync_repository(repo)

    return SyncResponse(**result)


@router.post("/{repo_id}/webhook")
async def configure_webhook(
    repo_id: int,
    config: WebhookConfig,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """配置 Webhook"""
    repo = await db.get(Repository, repo_id)
    if not repo:
        raise NotFoundError("Repository", repo_id)

    repo.webhook_enabled = config.enabled

    # 加密 secret
    if config.secret:
        repo.webhook_secret = encryption.encrypt(config.secret)
    elif not config.enabled:
        repo.webhook_secret = None

    await db.commit()

    return {
        "message": "Webhook configured",
        "enabled": config.enabled
    }
