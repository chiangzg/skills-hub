"""
SkillFile 模型 - Skill 文件索引
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class SkillFile(Base):
    """Skill 文件索引模型"""

    __tablename__ = "skill_files"

    id = Column(Integer, primary_key=True, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)  # 相对于 Skill 目录的文件路径
    file_name = Column(String(255), nullable=False)  # 文件名
    file_size = Column(Integer, default=0, nullable=False)  # 文件大小（字节）
    file_type = Column(String(50), default="text", nullable=False)  # 文件类型
    is_main = Column(Boolean, default=False, nullable=False)  # 是否为主文件 SKILL.md
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关联的 Skill
    skill = relationship("Skill", back_populates="files")

    def __repr__(self):
        return f"<SkillFile(id={self.id}, skill_id={self.skill_id}, path='{self.file_path}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "is_main": self.is_main,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
