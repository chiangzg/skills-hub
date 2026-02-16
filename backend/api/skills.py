"""
Skill API（前台公开接口）
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Skill, Category
from schemas.skill import SkillResponse, SkillListResponse, SkillSearchParams
from middleware.auth import get_optional_user
from core import logger

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.get("", response_model=SkillListResponse)
async def list_skills(
    keyword: str | None = None,
    category_id: int | None = None,
    repository_id: int | None = None,
    uncategorized: bool = False,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """搜索/浏览 Skills
    
    Args:
        uncategorized: 为 True 时返回未分配任何分类的技能（与 category_id 互斥，优先级更高）
    """
    # 构建查询
    query = select(Skill).options(
        selectinload(Skill.categories),
        selectinload(Skill.repository)
    )

    # 关键词搜索（使用 FULLTEXT 或 LIKE）
    if keyword:
        if hasattr(Skill, "__table__"):  # 确保有表
            # MySQL FULLTEXT 搜索（如果支持）
            # query = query.where(func.match(Skill.name, Skill.description).against(keyword))
            # 降级使用 LIKE
            query = query.where(
                or_(
                    Skill.name.like(f"%{keyword}%"),
                    Skill.description.like(f"%{keyword}%")
                )
            )

    # 分类筛选（uncategorized 与 category_id 互斥，uncategorized 优先）
    if uncategorized:
        # 查询没有关联任何分类的技能
        query = query.where(~Skill.categories.any())
    elif category_id:
        query = query.join(Skill.categories).where(Category.id == category_id)

    # 仓库筛选
    if repository_id:
        query = query.where(Skill.repository_id == repository_id)

    # 计算总数
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 排序
    sort_column = getattr(Skill, sort_by, Skill.created_at)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # 分页
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    skills = result.scalars().all()

    # 转换为响应
    items = []
    for skill in skills:
        skill_dict = skill.to_dict(include_categories=True, include_repository=True)
        items.append(SkillResponse(**skill_dict))

    return SkillListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """获取 Skill 详情"""
    result = await db.execute(
        select(Skill)
        .options(selectinload(Skill.categories), selectinload(Skill.repository))
        .where(Skill.id == skill_id)
    )
    skill = result.scalar_one_or_none()
    if not skill:
        from core import NotFoundError
        raise NotFoundError("Skill", skill_id)

    # 增加浏览计数
    skill.views += 1
    await db.commit()

    skill_dict = skill.to_dict(include_categories=True, include_repository=True, include_cache=True)
    return SkillResponse(**skill_dict)


@router.post("/{skill_id}/view")
async def increment_views(
    skill_id: int,
    db: AsyncSession = Depends(get_db)
):
    """增加 Skill 浏览次数"""
    skill = await db.get(Skill, skill_id)
    if skill:
        skill.views += 1
        await db.commit()

    return {"views": skill.views}


@router.get("/sync/pending")
async def get_pending_skills(
    current_user: User = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """获取待分配分类的 Skills"""
    # 获取没有分配任何分类的 skills
    from sqlalchemy import not_

    subquery = select(Skill).outerjoin(Skill.categories).where(Category.id.is_(None))
    result = await db.execute(subquery)
    skills = result.scalars().all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "directory": s.directory,
            "repository": f"{s.repo_owner}/{s.repo_name}" if s.repo_owner and s.repo_name else None
        }
        for s in skills
    ]
