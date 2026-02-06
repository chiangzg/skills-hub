"""
仓库管理 API
"""
import re
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Repository, RepositoryType
from schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    WebhookConfig,
    SyncResponse
)
from middleware.auth import get_current_user
from services.scanner import SkillScanner
from services.gitlab import get_gitlab_service
from core import NotFoundError, ConflictError, encryption
from core.security import generate_encryption_key

router = APIRouter(prefix="/api/admin/repositories", tags=["Repositories"])


def _parse_gitlab_url(gitlab_url: str) -> tuple[str, str | None, str | None]:
    """
    解析 GitLab URL，提取实例地址、owner 和 name

    支持的格式：
    - https://gitlab.example.com (仅实例地址)
    - https://gitlab.example.com/owner/name (完整仓库 URL)
    - https://gitlab.example.com/group/subgroup/name (嵌套组)

    Returns:
        (gitlab_base_url, owner, name)
    """
    # 移除末尾斜杠
    gitlab_url = gitlab_url.rstrip('/')

    # 解析 URL
    parsed = urlparse(gitlab_url)

    # 基础实例地址
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    # 提取路径部分
    path = parsed.path.lstrip('/')

    if not path:
        # 只有实例地址，没有 owner/name
        return base_url, None, None

    # 分割路径
    parts = path.split('/')

    if len(parts) >= 2:
        # 有 owner/name 或 group/subgroup/name
        owner = parts[0]
        name = parts[-1]  # 最后一个是仓库名
        return base_url, owner, name

    # 只有一个部分，无法确定 owner 和 name
    return base_url, None, None


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
    actual_owner = repo_data.owner
    actual_name = repo_data.name
    actual_branch = repo_data.branch
    actual_gitlab_url = repo_data.gitlab_url  # 存储到数据库的 URL

    if repo_data.type == RepositoryType.GITLAB:
        # 解析 gitlab_url，可能是完整 URL 或仅实例地址
        if repo_data.gitlab_url:
            gitlab_base_url, url_owner, url_name = _parse_gitlab_url(repo_data.gitlab_url)

            # 如果 URL 中包含 owner/name，使用它们
            if url_owner and url_name:
                actual_owner = url_owner
                actual_name = url_name

            # 存储正确的 GitLab 实例地址（不包含路径）
            actual_gitlab_url = gitlab_base_url

            # 通过 GitLab API 验证并获取正确的路径信息
            # 解决 owner 字段存储的是中文显示名称但实际 URL 需要使用用户路径的问题
            gitlab = get_gitlab_service(actual_gitlab_url)
            validation = await gitlab.validate_repository(
                owner=actual_owner,
                name=actual_name,
                branch=actual_branch,
                access_token=repo_data.access_token
            )

            if validation.get("exists") and validation.get("path_with_namespace"):
                path_parts = validation["path_with_namespace"].split("/")
                actual_owner = path_parts[0]
                actual_name = path_parts[-1] if len(path_parts) > 1 else actual_name
                if validation.get("default_branch"):
                    actual_branch = validation["default_branch"]

    # 检查是否已存在（使用实际的 owner/name）
    result = await db.execute(
        select(Repository).where(
            Repository.owner == actual_owner,
            Repository.name == actual_name,
            Repository.branch == actual_branch
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
        owner=actual_owner,
        name=actual_name,
        branch=actual_branch,
        gitlab_url=actual_gitlab_url,  # 存储正确的实例地址
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
