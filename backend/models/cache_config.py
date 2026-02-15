"""
CacheConfig 模型 - 缓存配置
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from database import Base


class CacheConfig(Base):
    """缓存配置模型"""

    __tablename__ = "cache_config"

    id = Column(Integer, primary_key=True, index=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<CacheConfig(key='{self.config_key}', value='{self.config_value[:50]}...')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_defaults(cls) -> dict:
        """获取默认配置"""
        return {
            "cache_base_path": "./cache",
            "max_cache_size_gb": "10",
            "max_file_size_mb": "10",
            "max_skill_size_mb": "50",
            "cleanup_strategy": "lru",
            "skill_hub_url": "http://localhost:8000",
            "skill_download_dir": "./skills"
        }
