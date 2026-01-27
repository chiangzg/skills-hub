"""
用户管理 API（仅管理员）
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from schemas.user import UserCreate, UserUpdate, UserResponse, PasswordReset
from middleware.auth import get_current_user, require_admin
from core import NotFoundError

router = APIRouter(prefix="/api/admin/users", tags=["Users"])


@router.get("", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserResponse(**u.to_dict()) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建新用户"""
    user = await auth_service.register(db, user_data, creator=current_user)
    return UserResponse(**user.to_dict())


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户详情"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return UserResponse(**user.to_dict())


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)

    if user_data.email is not None:
        user.email = user_data.email
    if user_data.is_active is not None:
        user.is_active = user_data.is_active

    await db.commit()
    await db.refresh(user)
    return UserResponse(**user.to_dict())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    if user_id == current_user.id:
        from core import SkillsException
        raise SkillsException("Cannot delete yourself", status_code=400)

    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)

    await db.delete(user)
    await db.commit()


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    data: PasswordReset,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """管理员重置用户密码"""
    user = await db.get(User, user_id)
    if not user:
        raise NotFoundError("User", user_id)

    await auth_service.reset_password(db, user, data.new_password)
    return {"message": "Password reset successfully"}


# 循环导入避免
from services.auth import auth_service
