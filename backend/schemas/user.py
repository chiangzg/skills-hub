"""
用户相关的 Pydantic Schema
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """用户基础 Schema"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr | None = None


class UserCreate(UserBase):
    """创建用户 Schema"""
    password: str = Field(..., min_length=8, max_length=100)
    role: str = Field(default="maintainer", pattern=r"^(admin|maintainer)$")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """用户登录 Schema"""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    """更新用户信息 Schema"""
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """用户响应 Schema"""
    id: int
    role: str
    is_active: bool
    created_at: str
    created_by: int | None = None

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """修改密码 Schema"""
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证新密码强度"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class PasswordReset(BaseModel):
    """重置密码 Schema（管理员操作）"""
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证新密码强度"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class TokenResponse(BaseModel):
    """Token 响应 Schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
