"""
公开分类 API（无需认证）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import Category, Skill
from schemas.category import CategoryResponse, CategoryTreeItem
from middleware.auth import get_optional_user
from models.user import User

router = APIRouter(prefix="/api/categories", tags=["Public Categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db)
):
    """获取所有分类（公开）"""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.skills))
        .order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    return [
        CategoryResponse(
            id=c.id,
            parent_id=c.parent_id,
            name=c.name,
            slug=c.slug,
            description=c.description,
            icon=c.icon,
            sort_order=c.sort_order,
            created_at=c.created_at.isoformat() if c.created_at else None,
            skill_count=len(c.skills),
            children=[]
        )
        for c in categories
    ]


@router.get("/tree", response_model=list[CategoryTreeItem])
async def get_category_tree(
    db: AsyncSession = Depends(get_db)
):
    """获取分类树（公开）"""
    # 获取所有顶级分类
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.skills), selectinload(Category.children))
        .where(Category.parent_id.is_(None))
        .order_by(Category.sort_order)
    )
    root_categories = result.scalars().all()

    tree = []
    for cat in root_categories:
        tree.append(CategoryTreeItem.from_orm_with_tree(
            cat,
            include_children=True,
            include_skill_count=True
        ))

    return tree


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取分类详情（公开）"""
    from core import NotFoundError

    result = await db.execute(
        select(Category)
        .options(selectinload(Category.skills))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category", category_id)

    return CategoryResponse(
        id=category.id,
        parent_id=category.parent_id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        created_at=category.created_at.isoformat() if category.created_at else None,
        skill_count=len(category.skills),
        children=[]
    )


@router.get("/{slug}/skills", response_model=list)
async def get_category_skills(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """获取分类下的 Skills（公开）"""
    from core import NotFoundError
    from schemas.skill import SkillResponse

    # 根据 slug 查找分类
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.skills))
        .where(Category.slug == slug)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category", slug)

    # 获取该分类的所有 skills（包括子分类）
    skills = []
    for skill in category.skills:
        skill_dict = skill.to_dict(include_categories=True, include_repository=True)
        skills.append(SkillResponse(**skill_dict))

    return skills
