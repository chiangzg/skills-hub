"""
Webhook API
"""
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Repository
from services.webhook import get_webhook_service
from core import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/gitlab/{repo_id}")
async def gitlab_webhook(
    repo_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    GitLab Webhook 接收端点

    在 GitLab 中配置：
    URL: http://your-server/webhooks/gitlab/{repo_id}
    Secret Token: (与仓库配置的 webhook_secret 一致)
    Trigger events: Push events
    """
    # 获取仓库
    repo = await db.get(Repository, repo_id)
    if not repo:
        logger.warning(f"Webhook for non-existent repository: {repo_id}")
        # 为了安全，不暴露仓库是否存在
        raise HTTPException(status_code=404, detail="Not found")

    # 验证签名
    signature = request.headers.get('X-Gitlab-Token')
    if repo.webhook_secret and signature != repo.webhook_secret:
        logger.warning(f"Invalid webhook signature for repository: {repo_id}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    # 获取事件类型
    event_type = request.headers.get('X-Gitlab-Event')
    logger.info(f"Received {event_type} webhook for repository {repo.full_name}")

    # 读取 payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # 异步处理 Push 事件
    if event_type == 'Push Hook':
        webhook_service = get_webhook_service(db)

        # 在后台任务中处理
        async def process_push():
            await webhook_service.handle_gitlab_push(repo_id, payload)

        background_tasks.add_task(process_push)

    return {"status": "accepted", "message": "Webhook received"}


@router.get("/logs")
async def get_webhook_logs(
    repo_id: int | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """获取 Webhook 日志"""
    webhook_service = get_webhook_service(db)
    logs = await webhook_service.get_webhook_logs(repo_id, limit)

    return [
        {
            "id": log.id,
            "repository_id": log.repository_id,
            "event_type": log.event_type,
            "status": log.status.value if hasattr(log.status, 'value') else log.status,
            "error_message": log.error_message,
            "triggered_at": log.triggered_at.isoformat() if log.triggered_at else None,
            "processed_at": log.processed_at.isoformat() if log.processed_at else None,
            "has_payload": bool(log.payload)
        }
        for log in logs
    ]
