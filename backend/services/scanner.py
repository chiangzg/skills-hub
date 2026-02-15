"""
Skill 扫描服务
扫描仓库中的所有 Skills，并管理本地缓存
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models import Repository, RepositoryType, Skill, SkillFile
from services.github import github_service
from services.gitlab import get_gitlab_service
from services.parser import skill_parser, SkillMetadata
from services.cache import CacheService
from schemas.skill import SkillMetadata as SchemaSkillMetadata
from core import logger, NotFoundError, ExternalServiceError, encryption


class SkillScanner:
    """Skill 扫描服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache_service = CacheService(db)

    async def scan_repository(
        self,
        repo: Repository,
        temp_dir: Path | None = None,
        keep_cache: bool = True
    ) -> List[SchemaSkillMetadata]:
        """
        扫描仓库中的所有 Skills

        Args:
            repo: 仓库模型
            temp_dir: 临时目录（可选）
            keep_cache: 是否保留缓存（默认 True）

        Returns:
            发现的 Skill 元数据列表
        """
        logger.info(f"Scanning repository: {repo.full_name}")

        # 1. 下载仓库
        extract_dir = await self._download_repo(repo, temp_dir)

        try:
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

        finally:
            # 3. 清理临时目录（仅在 keep_cache=False 时）
            if not keep_cache:
                cleanup_dir = extract_dir.parent if temp_dir is None else None
                if cleanup_dir and cleanup_dir.exists():
                    try:
                        shutil.rmtree(cleanup_dir)
                        logger.info(f"Cleaned up temporary directory: {cleanup_dir}")
                    except Exception as e:
                        logger.warning(f"Failed to cleanup temporary directory {cleanup_dir}: {e}")

    async def sync_repository(self, repo: Repository) -> dict:
        """
        同步仓库：下载、缓存、扫描并更新数据库

        Args:
            repo: 仓库模型

        Returns:
            同步结果统计
        """
        logger.info(f"Syncing repository: {repo.full_name}")

        # 初始化缓存服务
        await self.cache_service.initialize()

        # 1. 下载仓库并获取 zip 数据用于计算 Hash
        zip_data, extract_dir = await self._download_repo_with_data(repo)

        # 2. 计算压缩包 Hash
        zip_hash = self.cache_service.calculate_hash_from_bytes(zip_data)
        logger.info(f"Repository {repo.full_name} zip hash: {zip_hash[:12]}")

        # 3. 检查版本是否变化
        if repo.cache_version == zip_hash:
            logger.info(f"Repository {repo.full_name} unchanged (hash: {zip_hash[:12]}), skipping cache update")
            cache_path = self.cache_service.get_cache_path(repo)
            extract_dir_to_scan = cache_path / "current"
            
            if not extract_dir_to_scan.exists():
                # 如果 current 不存在，需要重新缓存
                logger.warning(f"Cache directory missing, re-caching...")
                extract_dir_to_scan = await self.cache_service.store_repository(
                    repo, extract_dir, zip_hash
                )
            else:
                # 清理临时目录
                try:
                    shutil.rmtree(extract_dir.parent)
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")
        else:
            # 4. 版本变化，更新缓存
            logger.info(f"Repository {repo.full_name} changed, updating cache...")
            extract_dir_to_scan = await self.cache_service.store_repository(
                repo, extract_dir, zip_hash
            )

        # 5. 扫描 Skill 目录
        skills_metadata = []
        for root, dirs, files in os.walk(extract_dir_to_scan):
            dirs[:] = [d for d in dirs if not d.startswith('.')]

            if 'SKILL.md' in files:
                skill_md_path = Path(root) / 'SKILL.md'
                metadata = skill_parser.parse_file(skill_md_path)

                rel_path = Path(root).relative_to(extract_dir_to_scan)

                skills_metadata.append(SchemaSkillMetadata(
                    name=metadata.name or rel_path.name,
                    description=metadata.description,
                    directory=str(rel_path),
                    tags=metadata.tags
                ))

        # 6. 更新数据库
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

            # 计算 Skill 的本地路径
            skill_local_path = str(self.cache_service.get_skill_cache_path(
                repo, metadata.directory
            ).absolute())

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

                # 更新本地路径
                if existing.local_path != skill_local_path:
                    existing.local_path = skill_local_path
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
                    local_path=skill_local_path,
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

        # 7. 索引 Skill 文件
        await self._index_all_skill_files(repo)

        logger.info(f"Sync completed: added={added}, updated={updated}, unchanged={unchanged}, removed={removed}")

        return {
            "status": "success",
            "skills_added": added,
            "skills_updated": updated,
            "skills_unchanged": unchanged,
            "skills_removed": removed,
            "cache_version": zip_hash[:12],
            "message": f"Synced {len(skills_metadata)} skills"
        }

    async def _index_all_skill_files(self, repo: Repository):
        """索引仓库中所有 Skill 的文件"""
        result = await self.db.execute(
            select(Skill).where(Skill.repository_id == repo.id)
        )
        skills = result.scalars().all()

        for skill in skills:
            try:
                await self.cache_service.index_skill_files(skill)
            except Exception as e:
                logger.warning(f"Failed to index files for skill {skill.name}: {e}")

    async def _download_repo(self, repo: Repository, temp_dir: Path | None = None) -> Path:
        """下载仓库到临时目录"""
        try:
            # 解密 access_token
            decrypted_token = None
            if repo.access_token:
                try:
                    decrypted_token = encryption.decrypt(repo.access_token)
                    logger.info(f"Successfully decrypted access token for {repo.full_name}")
                except Exception as e:
                    logger.error(f"Failed to decrypt access token for {repo.full_name}: {e}")
                    logger.error("This usually means the ENCRYPTION_KEY has changed. Please re-enter the access token.")
                    raise ExternalServiceError(
                        repo.type.value,
                        f"Access token decryption failed. The ENCRYPTION_KEY may have changed. Please re-enter the access token for this repository."
                    )

            if repo.type == RepositoryType.GITHUB:
                return await github_service.download_repo(
                    owner=repo.owner,
                    name=repo.name,
                    branch=repo.branch,
                    access_token=decrypted_token,
                    temp_dir=temp_dir
                )
            else:  # GITLAB
                gitlab = get_gitlab_service(repo.gitlab_url)
                return await gitlab.download_repo(
                    owner=repo.owner,
                    name=repo.name,
                    branch=repo.branch,
                    access_token=decrypted_token,
                    temp_dir=temp_dir
                )
        except ExternalServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to download repository {repo.full_name}: {e}")
            raise ExternalServiceError(repo.type.value, str(e))

    async def _download_repo_with_data(self, repo: Repository) -> tuple[bytes, Path]:
        """
        下载仓库并返回 zip 数据和解压目录
        
        Returns:
            (zip_data, extract_dir)
        """
        import aiofiles
        import httpx

        # 创建临时目录
        temp_dir = Path(tempfile.gettempdir())
        
        # 解密 access_token
        decrypted_token = None
        if repo.access_token:
            try:
                decrypted_token = encryption.decrypt(repo.access_token)
            except Exception as e:
                logger.error(f"Failed to decrypt access token for {repo.full_name}: {e}")
                raise ExternalServiceError(
                    repo.type.value,
                    "Access token decryption failed."
                )

        # 获取下载 URL
        if repo.type == RepositoryType.GITHUB:
            download_url = github_service.get_archive_url(
                repo.owner, repo.name, repo.branch
            )
            headers = {}
            if decrypted_token:
                headers["Authorization"] = f"token {decrypted_token}"
        else:  # GITLAB
            gitlab = get_gitlab_service(repo.gitlab_url)
            download_url = gitlab.get_archive_url(
                repo.owner, repo.name, repo.branch
            )
            headers = {}
            if decrypted_token:
                headers["PRIVATE-TOKEN"] = decrypted_token

        # 下载归档文件
        logger.info(f"Downloading repository from {download_url}")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(download_url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            archive_data = response.content

        # 判断文件类型并解压
        is_tarball = download_url.endswith('.tar.gz')
        extract_dir = temp_dir / f"{repo.owner}_{repo.name}_{repo.branch}"

        if is_tarball:
            import tarfile
            archive_path = temp_dir / f"{repo.owner}_{repo.name}_{repo.branch}.tar.gz"
            async with aiofiles.open(archive_path, "wb") as f:
                await f.write(archive_data)

            try:
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(extract_dir)

                items = list(extract_dir.iterdir())
                if items:
                    root_dir = items[0].name
                else:
                    root_dir = ""

                logger.info(f"Extracted tarball to {extract_dir}")
                return archive_data, extract_dir / root_dir

            except tarfile.TarError as e:
                raise ExternalServiceError(repo.type.value, f"Invalid tar.gz file: {e}")
            finally:
                if archive_path.exists():
                    archive_path.unlink()
        else:
            import zipfile
            archive_path = temp_dir / f"{repo.owner}_{repo.name}_{repo.branch}.zip"
            async with aiofiles.open(archive_path, "wb") as f:
                await f.write(archive_data)

            try:
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    namelist = zip_ref.namelist()
                    if namelist:
                        root_dir = namelist[0].split('/')[0]
                        zip_ref.extractall(extract_dir)
                    else:
                        root_dir = ""

                logger.info(f"Extracted zip to {extract_dir}")
                return archive_data, extract_dir / root_dir

            except zipfile.BadZipFile as e:
                raise ExternalServiceError(repo.type.value, f"Invalid zip file: {e}")
            finally:
                if archive_path.exists():
                    archive_path.unlink()

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
