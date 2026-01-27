"""
Skill 扫描服务
扫描仓库中的所有 Skills
"""
import os
from pathlib import Path
from typing import List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models import Repository, RepositoryType, Skill
from services.github import github_service
from services.gitlab import get_gitlab_service
from services.parser import skill_parser, SkillMetadata
from schemas.skill import SkillMetadata as SchemaSkillMetadata
from core import logger, NotFoundError, ExternalServiceError


class SkillScanner:
    """Skill 扫描服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_repository(
        self,
        repo: Repository,
        temp_dir: Path | None = None
    ) -> List[SchemaSkillMetadata]:
        """
        扫描仓库中的所有 Skills

        Args:
            repo: 仓库模型
            temp_dir: 临时目录（可选）

        Returns:
            发现的 Skill 元数据列表
        """
        logger.info(f"Scanning repository: {repo.full_name}")

        # 1. 下载仓库
        extract_dir = await self._download_repo(repo, temp_dir)

        # 2. 扫描目录
        skills = []
        for root, dirs, files in os.walk(extract_dir):
            # 跳过隐藏目录
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            if 'SKILL.md' in files:
                skill_md_path = Path(root) / 'SKILL.md'
                metadata = skill_parser.parse_file(skill_md_path)

                # 计算相对路径
                rel_path = Path(root).relative_to(extract_dir)

                skills.append(SchemaSkillMetadata(
                    name=metadata.name or rel_path.name,
                    description=metadata.description,
                    directory=str(rel_path),
                    tags=metadata.tags
                ))

        logger.info(f"Found {len(skills)} skills in {repo.full_name}")
        return skills

    async def sync_repository(self, repo: Repository) -> dict:
        """
        同步仓库：扫描并更新数据库

        Args:
            repo: 仓库模型

        Returns:
            同步结果统计
        """
        logger.info(f"Syncing repository: {repo.full_name}")

        # 下载并扫描
        skills_metadata = await self.scan_repository(repo)

        # 获取数据库中现有的 skills
        result = await self.db.execute(
            select(Skill).where(Skill.repository_id == repo.id)
        )
        existing_skills = {s.directory: s for s in result.scalars().all()}

        # 跟踪变更
        added = 0
        updated = 0
        unchanged = 0
        removed = 0

        # 处理发现的 skills
        found_directories = set()
        for metadata in skills_metadata:
            found_directories.add(metadata.directory)

            if metadata.directory in existing_skills:
                # 更新现有 skill
                existing = existing_skills[metadata.directory]
                changed = False

                if existing.name != (metadata.name or ""):
                    existing.name = metadata.name or existing.name
                    changed = True

                if existing.description != (metadata.description or ""):
                    existing.description = metadata.description
                    changed = True

                if changed:
                    existing.updated_at = datetime.utcnow()
                    updated += 1
                else:
                    unchanged += 1
            else:
                # 新增 skill
                skill = Skill(
                    repository_id=repo.id,
                    name=metadata.name or Path(metadata.directory).name,
                    description=metadata.description,
                    directory=metadata.directory,
                    repo_owner=repo.owner,
                    repo_name=repo.name,
                    repo_branch=repo.branch,
                    readme_url=self._build_readme_url(repo, metadata.directory),
                    raw_content_url=self._build_raw_url(repo, metadata.directory)
                )
                self.db.add(skill)
                added += 1

        # 删除不再存在的 skills
        for directory, skill in existing_skills.items():
            if directory not in found_directories:
                await self.db.delete(skill)
                removed += 1

        # 更新仓库的最后同步时间
        repo.last_sync_at = datetime.utcnow()

        await self.db.commit()

        logger.info(f"Sync completed: added={added}, updated={updated}, unchanged={unchanged}, removed={removed}")

        return {
            "status": "success",
            "skills_added": added,
            "skills_updated": updated,
            "skills_unchanged": unchanged,
            "skills_removed": removed,
            "message": f"Synced {len(skills_metadata)} skills"
        }

    async def _download_repo(self, repo: Repository, temp_dir: Path | None = None) -> Path:
        """下载仓库到临时目录"""
        try:
            if repo.type == RepositoryType.GITHUB:
                return await github_service.download_repo(
                    owner=repo.owner,
                    name=repo.name,
                    branch=repo.branch,
                    access_token=repo.access_token,
                    temp_dir=temp_dir
                )
            else:  # GITLAB
                gitlab = get_gitlab_service(repo.gitlab_url)
                return await gitlab.download_repo(
                    owner=repo.owner,
                    name=repo.name,
                    branch=repo.branch,
                    access_token=repo.access_token,
                    temp_dir=temp_dir
                )
        except Exception as e:
            logger.error(f"Failed to download repository {repo.full_name}: {e}")
            raise ExternalServiceError(repo.type.value, str(e))

    def _build_readme_url(self, repo: Repository, directory: str) -> str:
        """构建 README URL"""
        if repo.type == RepositoryType.GITHUB:
            return f"https://github.com/{repo.full_name}/tree/{repo.branch}/{directory}"
        else:  # GITLAB
            base_url = repo.gitlab_url or "https://gitlab.com"
            return f"{base_url}/{repo.full_name}/-/tree/{repo.branch}/{directory}"

    def _build_raw_url(self, repo: Repository, directory: str) -> str:
        """构建原始文件 URL"""
        if repo.type == RepositoryType.GITHUB:
            return f"https://github.com/{repo.full_name}/raw/{repo.branch}/{directory}/SKILL.md"
        else:  # GITLAB
            base_url = repo.gitlab_url or "https://gitlab.com"
            return f"{base_url}/{repo.full_name}/-/raw/{repo.branch}/{directory}/SKILL.md"
