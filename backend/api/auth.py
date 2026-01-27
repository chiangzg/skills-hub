"""
认证 API
"""
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import User
from schemas.user import (
    UserLogin,
    UserResponse,
    TokenResponse,
    PasswordChange,
    PasswordReset
)
from services.auth import auth_service
from middleware.auth import get_current_user, require_admin
from core import logger

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """用户登录"""
    user = await auth_service.authenticate(db, credentials.username, credentials.password)

    from middleware.auth import create_access_token
    access_token = create_access_token({"sub": str(user.id)})

    logger.info(f"User logged in: {user.username}")

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(**user.to_dict())
    )


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return UserResponse(**current_user.to_dict())


@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """修改当前用户密码"""
    await auth_service.change_password(
        db,
        current_user,
        data.old_password,
        data.new_password
    )
    return {"message": "Password changed successfully"}
