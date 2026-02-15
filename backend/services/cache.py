"""
缓存管理服务
管理 Skill 本地缓存的存储、读取和清理
"""
import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models import CacheConfig, Skill, SkillFile, Repository
from core import logger


class CacheService:
    """缓存管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._config_cache: Dict[str, str] = {}
        self._initialized = False

    async def initialize(self):
        """初始化缓存服务"""
        if self._initialized:
            return

        # 加载配置
        await self._load_config()
        
        # 确保缓存目录存在
        cache_base = self.get_config("cache_base_path", "./cache")
        cache_path = Path(cache_base)
        cache_path.mkdir(parents=True, exist_ok=True)
        
        # 创建 repos 子目录
        repos_path = cache_path / "repos"
        repos_path.mkdir(exist_ok=True)
        
        self._initialized = True
        logger.info(f"Cache service initialized at {cache_path.absolute()}")

    async def _load_config(self):
        """从数据库加载配置"""
        result = await self.db.execute(select(CacheConfig))
        configs = result.scalars().all()
        
        for config in configs:
            self._config_cache[config.config_key] = config.config_value
        
        # 合并默认配置
        defaults = CacheConfig.get_defaults()
        for key, value in defaults.items():
            if key not in self._config_cache:
                self._config_cache[key] = value

    def get_config(self, key: str, default: str = None) -> str:
        """获取配置值"""
        # 优先使用环境变量
        env_key = key.upper()
        env_value = os.environ.get(env_key)
        if env_value:
            return env_value
        
        # 其次使用缓存配置
        if key in self._config_cache:
            return self._config_cache[key]
        
        # 最后使用默认值
        return default

    def get_cache_path(self, repo: Repository) -> Path:
        """获取仓库的缓存路径"""
        cache_base = self.get_config("cache_base_path", "./cache")
        repo_type = repo.type.value.lower()
        safe_owner = self._safe_name(repo.owner)
        safe_name = self._safe_name(repo.name)
        safe_branch = self._safe_name(repo.branch)
        
        return Path(cache_base) / "repos" / f"{repo_type}_{safe_owner}_{safe_name}_{safe_branch}"

    def get_skill_cache_path(self, repo: Repository, skill_directory: str) -> Path:
        """获取 Skill 的缓存路径"""
        repo_cache_path = self.get_cache_path(repo)
        current_path = repo_cache_path / "current"
        return current_path / skill_directory

    @staticmethod
    def _safe_name(name: str) -> str:
        """将名称转换为安全的文件名"""
        if not name:
            return "unknown"
        # 替换不安全的字符
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        return safe.lower()

    @staticmethod
    def calculate_hash(file_path: Path) -> str:
        """计算文件的 MD5 Hash"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def calculate_hash_from_bytes(data: bytes) -> str:
        """计算字节数据的 MD5 Hash"""
        return hashlib.md5(data).hexdigest()

    async def store_repository(
        self,
        repo: Repository,
        extract_dir: Path,
        zip_hash: str
    ) -> Path:
        """
        存储仓库缓存
        
        Args:
            repo: 仓库模型
            extract_dir: 解压后的临时目录
            zip_hash: 压缩包的 Hash值
        
        Returns:
            最终存储路径
        """
        await self.initialize()
        
        cache_path = self.get_cache_path(repo)
        hash_short = zip_hash[:12]
        target_path = cache_path / hash_short
        current_link = cache_path / "current"
        
        # 检查版本是否变化
        if repo.cache_version == zip_hash and target_path.exists():
            logger.info(f"Repository {repo.full_name} cache unchanged, skipping")
            return target_path
        
        # 删除旧版本（保留 current 软链接）
        if cache_path.exists():
            for item in cache_path.iterdir():
                if item.name != "current":
                    try:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to remove old cache {item}: {e}")
        
        # 移动解压目录到目标位置
        if target_path.exists():
            shutil.rmtree(target_path)
        
        shutil.move(str(extract_dir), str(target_path))
        
        # 更新 current 软链接
        if current_link.exists() or current_link.is_symlink():
            current_link.unlink()
        
        # Windows 不支持 symlink，使用 junction 或直接复制
        if os.name == 'nt':
            # Windows: 使用目录 junction 或直接复制
            shutil.copytree(str(target_path), str(current_link))
        else:
            # Unix: 使用软链接
            current_link.symlink_to(hash_short)
        
        # 计算缓存大小
        cache_size = sum(f.stat().st_size for f in target_path.rglob('*') if f.is_file())
        
        # 更新仓库缓存信息
        repo.cache_version = zip_hash
        repo.cache_path = str(cache_path.absolute())
        repo.cache_size = cache_size
        
        await self.db.commit()
        
        logger.info(f"Repository {repo.full_name} cached at {target_path}, size: {cache_size} bytes")
        
        return target_path

    async def get_skill_files(self, skill: Skill) -> List[Dict[str, Any]]:
        """
        获取 Skill 的所有文件内容
        
        Args:
            skill: Skill 模型
        
        Returns:
            文件列表，每个文件包含 path, content, size, is_main
        """
        await self.initialize()
        
        if not skill.local_path:
            # 尝试构建本地路径
            if skill.repository:
                skill.local_path = str(self.get_skill_cache_path(
                    skill.repository, 
                    skill.directory
                ).absolute())
        
        skill_path = Path(skill.local_path) if skill.local_path else None
        
        if not skill_path or not skill_path.exists():
            logger.warning(f"Skill {skill.name} cache not found at {skill_path}")
            return []
        
        files = []
        max_file_size = int(self.get_config("max_file_size_mb", "10")) * 1024 * 1024
        max_skill_size = int(self.get_config("max_skill_size_mb", "50")) * 1024 * 1024
        total_size = 0
        
        for file_path in skill_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            # 跳过隐藏文件
            if file_path.name.startswith('.'):
                continue
            
            file_size = file_path.stat().st_size
            
            # 检查文件大小限制
            if file_size > max_file_size:
                logger.warning(f"File {file_path} exceeds size limit, skipping")
                continue
            
            # 检查总大小限制
            if total_size + file_size > max_skill_size:
                logger.warning(f"Skill {skill.name} total size exceeds limit, stopping")
                break
            
            # 读取文件内容
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # 跳过二进制文件
                logger.debug(f"Skipping binary file: {file_path}")
                continue
            except Exception as e:
                logger.warning(f"Failed to read file {file_path}: {e}")
                continue
            
            # 计算相对路径
            rel_path = file_path.relative_to(skill_path)
            
            files.append({
                "path": str(rel_path).replace("\\", "/"),  # 统一使用正斜杠
                "content": content,
                "size": file_size,
                "is_main": file_path.name.upper() == "SKILL.MD"
            })
            
            total_size += file_size
        
        return files

    async def index_skill_files(self, skill: Skill) -> int:
        """
        索引 Skill 的文件到数据库
        
        Args:
            skill: Skill 模型
        
        Returns:
            索引的文件数量
        """
        await self.initialize()
        
        # 删除旧的文件索引
        await self.db.execute(
            delete(SkillFile).where(SkillFile.skill_id == skill.id)
        )
        
        skill_path = Path(skill.local_path) if skill.local_path else None
        
        if not skill_path or not skill_path.exists():
            return 0
        
        indexed_count = 0
        
        for file_path in skill_path.rglob("*"):
            if not file_path.is_file():
                continue
            
            if file_path.name.startswith('.'):
                continue
            
            file_size = file_path.stat().st_size
            rel_path = file_path.relative_to(skill_path)
            
            # 判断文件类型
            file_ext = file_path.suffix.lower()
            file_type = self._get_file_type(file_ext)
            
            skill_file = SkillFile(
                skill_id=skill.id,
                file_path=str(rel_path).replace("\\", "/"),
                file_name=file_path.name,
                file_size=file_size,
                file_type=file_type,
                is_main=file_path.name.upper() == "SKILL.MD"
            )
            
            self.db.add(skill_file)
            indexed_count += 1
        
        await self.db.commit()
        
        logger.info(f"Indexed {indexed_count} files for skill {skill.name}")
        
        return indexed_count

    @staticmethod
    def _get_file_type(extension: str) -> str:
        """根据扩展名判断文件类型"""
        text_extensions = {
            '.md', '.txt', '.json', '.yaml', '.yml', '.xml',
            '.py', '.js', '.ts', '.html', '.css', '.sql',
            '.sh', '.bat', '.ps1', '.env', '.cfg', '.ini',
            '.markdown', '.rst', '.log'
        }
        
        if extension in text_extensions:
            return 'text'
        elif extension in {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'}:
            return 'image'
        elif extension in {'.pdf', '.doc', '.docx'}:
            return 'document'
        else:
            return 'other'

    async def cleanup_old_cache(self, max_size_gb: float = None):
        """
        清理旧缓存（LRU 策略）
        
        Args:
            max_size_gb: 最大缓存大小（GB）
        """
        if max_size_gb is None:
            max_size_gb = float(self.get_config("max_cache_size_gb", "10"))
        
        max_size_bytes = max_size_gb * 1024 * 1024 * 1024
        
        # 获取所有仓库的缓存信息
        result = await self.db.execute(
            select(Repository).where(Repository.cache_path.isnot(None))
        )
        repos = result.scalars().all()
        
        # 计算总大小
        total_size = sum(repo.cache_size or 0 for repo in repos)
        
        if total_size <= max_size_bytes:
            return
        
        # 按最后同步时间排序（最旧的优先清理）
        repos.sort(key=lambda r: r.last_sync_at or datetime.min)
        
        for repo in repos:
            if total_size <= max_size_bytes:
                break
            
            # 清理该仓库的缓存
            if repo.cache_path:
                cache_path = Path(repo.cache_path)
                if cache_path.exists():
                    repo_size = repo.cache_size or 0
                    shutil.rmtree(cache_path)
                    repo.cache_path = None
                    repo.cache_version = None
                    repo.cache_size = 0
                    total_size -= repo_size
                    logger.info(f"Cleaned up cache for repository {repo.full_name}")
        
        await self.db.commit()

    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        result = await self.db.execute(
            select(Repository).where(Repository.cache_path.isnot(None))
        )
        repos = result.scalars().all()
        
        total_size = sum(repo.cache_size or 0 for repo in repos)
        cached_count = len(repos)
        
        return {
            "total_repositories": cached_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 2),
            "repositories": [
                {
                    "id": r.id,
                    "name": r.full_name,
                    "cache_version": r.cache_version,
                    "cache_size": r.cache_size,
                    "last_sync_at": r.last_sync_at.isoformat() if r.last_sync_at else None
                }
                for r in repos
            ]
        }
