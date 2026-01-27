"""
认证服务
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from models.user import User, UserRole
from schemas.user import UserCreate, UserResponse
from core import (
    password_manager,
    SkillsException,
    ConflictError,
    ValidationError,
    logger
)


class AuthService:
    """认证服务"""

    async def register(
        self,
        db: AsyncSession,
        user_data: UserCreate,
        creator: User | None = None
    ) -> User:
        """
        注册新用户
        creator: 创建者（admin用户），只有 admin 可以创建新用户
        """
        # 检查用户名是否已存在
        result = await db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            raise ConflictError(
                message="Username already exists",
                resource="user",
                field="username"
            )

        # 检查创建者权限
        if user_data.role == UserRole.ADMIN and (not creator or not creator.is_admin):
            raise ValidationError("Only admins can create admin users")

        # 创建新用户
        user = User(
            username=user_data.username,
            password_hash=password_manager.hash_password(user_data.password),
            email=user_data.email,
            role=UserRole(user_data.role),
            is_active=True,
            created_by=creator.id if creator else None
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"New user created: {user.username} (role: {user.role})")
        return user

    async def authenticate(
        self,
        db: AsyncSession,
        username: str,
        password: str
    ) -> User:
        """验证用户凭据"""
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise SkillsException(
                message="Invalid username or password",
                code="AUTHENTICATION_FAILED",
                status_code=401
            )

        if not user.is_active:
            raise SkillsException(
                message="User account is disabled",
                code="ACCOUNT_DISABLED",
                status_code=401
            )

        if not password_manager.verify_password(password, user.password_hash):
            raise SkillsException(
                message="Invalid username or password",
                code="AUTHENTICATION_FAILED",
                status_code=401
            )

        logger.info(f"User authenticated: {user.username}")
        return user

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        old_password: str,
        new_password: str
    ) -> None:
        """修改密码"""
        if not password_manager.verify_password(old_password, user.password_hash):
            raise ValidationError("Current password is incorrect")

        user.password_hash = password_manager.hash_password(new_password)
        await db.commit()

        logger.info(f"Password changed for user: {user.username}")

    async def reset_password(
        self,
        db: AsyncSession,
        user: User,
        new_password: str
    ) -> None:
        """管理员重置用户密码"""
        user.password_hash = password_manager.hash_password(new_password)
        await db.commit()

        logger.info(f"Password reset for user: {user.username} (by admin)")


auth_service = AuthService()
