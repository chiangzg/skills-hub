"""
Skill 模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Skill(Base):
    """Skill 模型"""

    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    directory = Column(String(500), nullable=False)
    repo_owner = Column(String(100), nullable=True)
    repo_name = Column(String(100), nullable=True)
    repo_branch = Column(String(50), nullable=True)
    readme_url = Column(Text, nullable=True)
    raw_content_url = Column(Text, nullable=True)
    stars = Column(Integer, default=0, nullable=False)
    views = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关联的仓库
    repository = relationship("Repository", back_populates="skills")

    # 多对多关系：所属分类
    categories = relationship(
        "Category",
        secondary="category_skills",
        back_populates="skills"
    )

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', directory='{self.directory}')>"

    def to_dict(self, include_categories: bool = False, include_repository: bool = False) -> dict:
        """转换为字典"""
        data = {
            "id": self.id,
            "repository_id": self.repository_id,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "directory": self.directory,
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "repo_branch": self.repo_branch,
            "readme_url": self.readme_url,
            "raw_content_url": self.raw_content_url,
            "stars": self.stars,
            "views": self.views,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

        # 生成 CLI 命令（使用仓库 clone_url）
        if include_repository and self.repository:
            clone_url = self.repository.clone_url
            data["cli_command"] = f"/skill:skill-install {clone_url} {self.name}"
            data["repository"] = {
                "type": self.repository.type.value,
                "owner": self.repository.owner,
                "name": self.repository.name,
                "full_name": self.repository.full_name
            }

        if include_categories and self.categories:
            data["categories"] = [
                {"id": c.id, "name": c.name, "slug": c.slug}
                for c in self.categories
            ]

        return data

    @property
    def key(self) -> str:
        """Skill 的唯一标识"""
        if self.repo_owner and self.repo_name:
            return f"{self.repo_owner}/{self.repo_name}:{self.directory}"
        return f"unknown:{self.directory}"

    async def increment_views(self, db):
        """增加浏览次数"""
        self.views += 1
        await db.commit()
