"""
分类相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """分类基础 Schema"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int = Field(default=0)


class CategoryCreate(CategoryBase):
    """创建分类 Schema"""
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    """更新分类 Schema - 所有字段可选"""
    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    description: str | None = None
    icon: str | None = Field(None, max_length=50)
    sort_order: int | None = None
    parent_id: int | None = None


class CategoryResponse(CategoryBase):
    """分类响应 Schema"""
    id: int
    parent_id: int | None
    created_at: str
    skill_count: int = 0
    children: list["CategoryResponse"] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_with_tree(cls, category, include_children: bool = True, include_skill_count: bool = False):
        """从 ORM 对象创建响应（包含子树）"""
        # 安全获取 skill_count，避免触发懒加载
        skill_count = 0
        if include_skill_count:
            try:
                if hasattr(category, 'skills') and category.skills:
                    skill_count = len(category.skills)
            except Exception:
                # 如果 skills 没有预加载，返回 0
                skill_count = 0

        data = {
            "id": category.id,
            "parent_id": category.parent_id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "icon": category.icon,
            "sort_order": category.sort_order,
            "created_at": category.created_at.isoformat() if category.created_at else None,
            "skill_count": skill_count,
            "children": []
        }

        if include_children and hasattr(category, 'children') and category.children:
            data["children"] = [
                cls.from_orm_with_tree(
                    child,
                    include_children=False,
                    include_skill_count=False  # 子分类不加载 skill_count，避免懒加载
                )
                for child in sorted(category.children, key=lambda c: c.sort_order)
            ]

        return cls(**data)


class CategoryTreeItem(CategoryResponse):
    """分类树项（递归结构）"""
    pass


# 更新前向引用
CategoryResponse.model_rebuild()


class AssignCategories(BaseModel):
    """分配分类 Schema"""
    category_ids: list[int] = Field(..., min_length=1)
