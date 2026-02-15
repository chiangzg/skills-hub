"""
仓库模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class RepositoryType(str, enum.Enum):
    """仓库类型枚举"""
    GITHUB = "GITHUB"
    GITLAB = "GITLAB"


class Repository(Base):
    """仓库模型"""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(RepositoryType), nullable=False)
    owner = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    branch = Column(String(50), default="main", nullable=False)
    gitlab_url = Column(String(255), nullable=True)  # GitLab 自建实例地址
    access_token = Column(String(255), nullable=True)  # 加密存储
    webhook_secret = Column(String(255), nullable=True)
    webhook_enabled = Column(Boolean, default=False, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    # 缓存相关字段
    cache_version = Column(String(64), nullable=True)  # 缓存版本标识（压缩包Hash）
    cache_path = Column(String(500), nullable=True)  # 本地缓存绝对路径
    cache_size = Column(Integer, default=0, nullable=False)  # 缓存占用空间（字节）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关联的 skills
    skills = relationship("Skill", back_populates="repository", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repository(id={self.id}, type='{self.type}', owner='{self.owner}', name='{self.name}')>"

    def to_dict(self) -> dict:
        """转换为字典（用于 API 响应）"""
        return {
            "id": self.id,
            "type": self.type.value if isinstance(self.type, enum.Enum) else self.type,
            "owner": self.owner,
            "name": self.name,
            "branch": self.branch,
            "gitlab_url": self.gitlab_url,
            "webhook_enabled": self.webhook_enabled,
            "enabled": self.enabled,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            # 缓存信息
            "cache_version": self.cache_version,
            "cache_path": self.cache_path,
            "cache_size": self.cache_size,
            "is_cached": bool(self.cache_path),
            # 不返回敏感信息
            "has_token": bool(self.access_token),
            "has_webhook_secret": bool(self.webhook_secret)
        }

    @property
    def full_name(self) -> str:
        """完整仓库名（owner/name）"""
        return f"{self.owner}/{self.name}"

    @property
    def clone_url(self) -> str:
        """获取克隆 URL"""
        type_value = self.type.value if isinstance(self.type, enum.Enum) else self.type
        if type_value == "GITHUB":
            return f"https://github.com/{self.full_name}.git"
        else:  # GITLAB
            base_url = self.gitlab_url.rstrip('/') if self.gitlab_url else "https://gitlab.com"
            return f"{base_url}/{self.full_name}.git"
