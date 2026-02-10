"""
认证服务测试用例
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, UserRole
from services.auth import auth_service
from schemas.user import UserCreate
from core import ConflictError, ValidationError, SkillsException


class TestAuthService:
    """AuthService 测试类"""

    async def test_register_new_user_success(self, db: AsyncSession):
        """测试成功注册新用户"""
        user_data = UserCreate(
            username="testuser",
            password="TestPassword123!",
            email="test@example.com",
            role="maintainer"
        )

        user = await auth_service.register(db, user_data)

        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.MAINTAINER
        assert user.is_active is True
        assert user.password_hash != "TestPassword123!"  # Password should be hashed

    async def test_register_duplicate_username_fails(self, db: AsyncSession):
        """测试重复用户名注册失败"""
        user_data = UserCreate(
            username="duplicate",
            password="TestPassword123!",
            role="maintainer"
        )

        # First registration should succeed
        await auth_service.register(db, user_data)

        # Second registration with same username should fail
        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register(db, user_data)

        assert "username" in str(exc_info.value).lower()

    async def test_register_admin_by_non_admin_fails(self, db: AsyncSession):
        """测试非管理员用户不能创建管理员账户"""
        # Create a regular maintainer user
        maintainer_data = UserCreate(
            username="maintainer",
            password="TestPassword123!",
            role="maintainer"
        )
        maintainer = await auth_service.register(db, maintainer_data)

        # Try to create admin user as maintainer (should fail)
        admin_data = UserCreate(
            username="admin_attempt",
            password="TestPassword123!",
            role="admin"
        )

        with pytest.raises(ValidationError) as exc_info:
            await auth_service.register(db, admin_data, creator=maintainer)

        assert "admin" in str(exc_info.value).lower()

    async def test_register_admin_by_admin_succeeds(self, db: AsyncSession):
        """测试管理员可以创建管理员账户"""
        # Create an admin user first
        admin_data = UserCreate(
            username="superadmin",
            password="TestPassword123!",
            role="admin"
        )
        admin = await auth_service.register(db, admin_data)

        # Create another admin via existing admin
        new_admin_data = UserCreate(
            username="newadmin",
            password="TestPassword123!",
            role="admin"
        )

        new_admin = await auth_service.register(db, new_admin_data, creator=admin)

        assert new_admin.role == UserRole.ADMIN
        assert new_admin.created_by == admin.id

    async def test_authenticate_with_valid_credentials(self, db: AsyncSession):
        """测试有效凭据认证"""
        user_data = UserCreate(
            username="authuser",
            password="ValidPassword123!",
            role="maintainer"
        )
        await auth_service.register(db, user_data)

        user = await auth_service.authenticate(
            db,
            username="authuser",
            password="ValidPassword123!"
        )

        assert user.username == "authuser"
        assert user.is_active is True

    async def test_authenticate_with_invalid_username(self, db: AsyncSession):
        """测试无效用户名认证失败"""
        with pytest.raises(SkillsException) as exc_info:
            await auth_service.authenticate(db, username="nonexistent", password="anypassword")

        assert exc_info.value.status_code == 401

    async def test_authenticate_with_invalid_password(self, db: AsyncSession):
        """测试无效密码认证失败"""
        user_data = UserCreate(
            username="wrongpass",
            password="CorrectPassword123!",
            role="maintainer"
        )
        await auth_service.register(db, user_data)

        with pytest.raises(SkillsException) as exc_info:
            await auth_service.authenticate(db, username="wrongpass", password="WrongPassword!")

        assert exc_info.value.status_code == 401

    async def test_authenticate_disabled_user_fails(self, db: AsyncSession):
        """测试禁用用户无法认证"""
        user_data = UserCreate(
            username="disabled",
            password="Password123!",
            role="maintainer"
        )
        user = await auth_service.register(db, user_data)

        # Disable the user
        user.is_active = False
        await db.commit()

        with pytest.raises(SkillsException) as exc_info:
            await auth_service.authenticate(db, username="disabled", password="Password123!")

        assert "disabled" in str(exc_info.value).lower()

    async def test_change_password_with_correct_old_password(self, db: AsyncSession):
        """测试使用正确的旧密码修改密码"""
        user_data = UserCreate(
            username="changepass",
            password="OldPassword123!",
            role="maintainer"
        )
        user = await auth_service.register(db, user_data)

        await auth_service.change_password(
            db, user,
            old_password="OldPassword123!",
            new_password="NewPassword456!"
        )

        # Verify new password works
        authenticated_user = await auth_service.authenticate(
            db, username="changepass", password="NewPassword456!"
        )
        assert authenticated_user.id == user.id

    async def test_change_password_with_incorrect_old_password_fails(self, db: AsyncSession):
        """测试使用错误的旧密码修改密码失败"""
        user_data = UserCreate(
            username="wrongold",
            password="Original123!",
            role="maintainer"
        )
        user = await auth_service.register(db, user_data)

        with pytest.raises(ValidationError):
            await auth_service.change_password(
                db, user,
                old_password="WrongPassword!",
                new_password="NewPassword456!"
            )

    async def test_reset_password_by_admin(self, db: AsyncSession):
        """测试管理员重置用户密码"""
        user_data = UserCreate(
            username="resetme",
            password="Original123!",
            role="maintainer"
        )
        user = await auth_service.register(db, user_data)

        await auth_service.reset_password(
            db, user,
            new_password="ResetPassword789!"
        )

        # Verify new password works
        authenticated_user = await auth_service.authenticate(
            db, username="resetme", password="ResetPassword789!"
        )
        assert authenticated_user.id == user.id


@pytest.fixture
async def db(test_db: AsyncSession):
    """数据库测试 fixture"""
    yield test_db
