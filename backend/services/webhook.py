"""
Webhook 处理服务
处理 GitLab Push 事件，触发自动同步
"""
from datetime import datetime
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import Repository, Webhook, WebhookStatus
from services.scanner import SkillScanner
from core import logger


class WebhookService:
    """Webhook 处理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    def verify_gitlab_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """
        验证 GitLab Webhook 签名

        GitLab 使用简单的 token 验证，通过 X-Gitlab-Token header 传递
        """
        if not secret:
            return True  # 如果没配置密钥，跳过验证
        return signature == secret

    async def handle_gitlab_push(
        self,
        repo_id: int,
        payload: dict
    ) -> Webhook:
        """
        处理 GitLab Push 事件

        GitLab Push 事件格式：
        https://docs.gitlab.com/ee/user/project/integrations/webhooks.html#push-events
        """
        # 记录 webhook 日志
        webhook_log = Webhook(
            repository_id=repo_id,
            event_type='push',
            payload=payload,
            status=WebhookStatus.PROCESSING
        )
        self.db.add(webhook_log)
        await self.db.commit()
        await self.db.refresh(webhook_log)

        try:
            # 获取仓库信息
            result = await self.db.execute(
                select(Repository).where(Repository.id == repo_id)
            )
            repo = result.scalar_one_or_none()

            if not repo:
                webhook_log.status = WebhookStatus.FAILED
                webhook_log.error_message = 'Repository not found'
                await self.db.commit()
                return webhook_log

            if not repo.webhook_enabled:
                webhook_log.status = WebhookStatus.FAILED
                webhook_log.error_message = 'Webhook disabled for this repository'
                await self.db.commit()
                return webhook_log

            # 提取分支信息
            ref = payload.get('ref', '')  # refs/heads/main
            branch = ref.replace('refs/heads/', '') if ref.startswith('refs/heads/') else ref

            # 只处理配置的分支
            if branch != repo.branch:
                webhook_log.status = WebhookStatus.SUCCESS
                webhook_log.error_message = f'Branch {branch} not matched (configured: {repo.branch}), skipping'
                await self.db.commit()
                logger.info(f"Webhook skipped: branch mismatch ({branch} != {repo.branch})")
                return webhook_log

            # 触发同步任务
            scanner = SkillScanner(self.db)
            sync_result = await scanner.sync_repository(repo)

            webhook_log.status = WebhookStatus.SUCCESS
            logger.info(f"Webhook sync completed: {sync_result}")

        except Exception as e:
            webhook_log.status = WebhookStatus.FAILED
            webhook_log.error_message = str(e)
            logger.error(f"Webhook processing failed: {e}", exc_info=True)

        finally:
            webhook_log.processed_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(webhook_log)

        return webhook_log

    async def get_webhook_logs(
        self,
        repository_id: int | None = None,
        limit: int = 100
    ) -> list[Webhook]:
        """获取 Webhook 日志"""
        query = select(Webhook).order_by(Webhook.triggered_at.desc())
        if repository_id:
            query = query.where(Webhook.repository_id == repository_id)
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())


webhook_service = None  # 将在运行时初始化


def get_webhook_service(db: AsyncSession) -> WebhookService:
    """获取 Webhook 服务实例"""
    return WebhookService(db)
