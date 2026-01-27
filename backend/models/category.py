"""
分类模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from datetime import datetime

from database import Base

# 多对多关联表（必须在模型类之前定义）
category_skills = Table(
    'category_skills',
    Base.metadata,
    Column('category_id', Integer, ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    Column('skill_id', Integer, ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True)
)


class Category(Base):
    """分类模型（支持多级分类）"""

    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 自引用关系
    children = relationship(
        "Category",
        backref=backref("parent", remote_side="Category.id"),
        cascade="all, delete-orphan"
    )

    # 多对多关系：分类包含的 skills
    skills = relationship(
        "Skill",
        secondary="category_skills",
        back_populates="categories",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}', slug='{self.slug}')>"

    def to_dict(self, include_children: bool = False, include_skill_count: bool = False) -> dict:
        """转换为字典"""
        data = {
            "id": self.id,
            "parent_id": self.parent_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "icon": self.icon,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

        if include_children and self.children:
            data["children"] = [
                child.to_dict(include_children=False)
                for child in sorted(self.children, key=lambda c: c.sort_order)
            ]

        if include_skill_count:
            data["skill_count"] = len(self.skills)

        return data

    async def get_ancestors(self, db) -> list:
        """获取所有祖先分类"""
        ancestors = []
        current = self
        while current.parent_id:
            current = await db.get(Category, current.parent_id)
            if current:
                ancestors.append(current)
            else:
                break
        return list(reversed(ancestors))

    async def get_descendants(self, db) -> list:
        """获取所有后代分类（递归）"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(await child.get_descendants(db))
        return descendants
