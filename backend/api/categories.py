"""
分类管理 API
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Category, Skill
from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryTreeItem,
    AssignCategories
)
from middleware.auth import get_current_user
from core import NotFoundError, ConflictError

router = APIRouter(prefix="/api/admin/categories", tags=["Categories"])


@router.get("/tree", response_model=list[CategoryTreeItem])
async def get_category_tree(
    current_user: User = Depends(get_current_user),
    db:AsyncSession = Depends(get_db)
):
    """获取分类树"""
    # 获取所有顶级分类，使用 selectinload 预加载 skills 和 children
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


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db:AsyncSession = Depends(get_db)
):
    """获取所有分类（平铺列表）"""
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


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """创建分类"""
    # 检查 slug 是否已存在
    result = await db.execute(
        select(Category).where(Category.slug == category_data.slug)
    )
    if result.scalar_one_or_none():
        raise ConflictError(
            message="Category with this slug already exists",
            resource="category",
            field="slug"
        )

    # 验证父分类存在
    if category_data.parent_id:
        parent = await db.get(Category, category_data.parent_id)
        if not parent:
            raise NotFoundError("Parent category", category_data.parent_id)

    category = Category(**category_data.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)

    return CategoryResponse(
        id=category.id,
        parent_id=category.parent_id,
        name=category.name,
        slug=category.slug,
        description=category.description,
        icon=category.icon,
        sort_order=category.sort_order,
        created_at=category.created_at.isoformat() if category.created_at else None,
        skill_count=0,
        children=[]
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db:AsyncSession = Depends(get_db)
):
    """获取分类详情"""
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


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db:AsyncSession = Depends(get_db)
):
    """更新分类"""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.skills))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Category", category_id)

    # 验证父分类（检查 parent_id 是否在更新数据中）
    update_dict = category_data.model_dump(exclude_unset=True)
    if 'parent_id' in update_dict:
        if update_dict['parent_id'] == category_id:
            from core import ValidationError
            raise ValidationError("Category cannot be its own parent")
        if update_dict['parent_id'] is not None:
            parent = await db.get(Category, update_dict['parent_id'])
            if not parent:
                raise NotFoundError("Parent category", update_dict['parent_id'])

    # 更新字段
    for field, value in update_dict.items():
        setattr(category, field, value)

    await db.commit()
    await db.refresh(category)

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


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """删除分类"""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundError("Category", category_id)

    await db.delete(category)
    await db.commit()


@router.post("/{category_id}/skills/{skill_id}")
async def assign_skill_to_category(
    category_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """将 Skill 分配到分类"""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundError("Category", category_id)

    skill = await db.get(Skill, skill_id)
    if not skill:
        raise NotFoundError("Skill", skill_id)

    if skill not in category.skills:
        category.skills.append(skill)
        await db.commit()

    return {"message": "Skill assigned to category"}


@router.delete("/{category_id}/skills/{skill_id}")
async def remove_skill_from_category(
    category_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """将 Skill 从分类中移除"""
    category = await db.get(Category, category_id)
    if not category:
        raise NotFoundError("Category", category_id)

    skill = await db.get(Skill, skill_id)
    if not skill:
        raise NotFoundError("Skill", skill_id)

    if skill in category.skills:
        category.skills.remove(skill)
        await db.commit()

    return {"message": "Skill removed from category"}


@router.post("/skills/{skill_id}/categories")
async def assign_skill_categories(
    skill_id: int,
    data: AssignCategories,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """为 Skill 分配多个分类"""
    from sqlalchemy.orm import selectinload

    result = await db.execute(
        select(Skill)
        .options(selectinload(Skill.categories))
        .where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise NotFoundError("Skill", skill_id)

    # 清除现有分类
    skill.categories.clear()

    # 添加新分类
    for cat_id in data.category_ids:
        category = await db.get(Category, cat_id)
        if category:
            skill.categories.append(category)

    await db.commit()

    return {"message": f"Assigned {len(data.category_ids)} categories to skill"}
