"""
用户模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    MAINTAINER = "maintainer"


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.MAINTAINER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"

    def to_dict(self, exclude: set = None) -> dict:
        """转换为字典（用于 API 响应）"""
        exclude = exclude or {"password_hash"}
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role.value if isinstance(self.role, enum.Enum) else self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by
        }

    @property
    def is_admin(self) -> bool:
        """是否是管理员"""
        return self.role == UserRole.ADMIN
