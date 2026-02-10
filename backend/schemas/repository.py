"""
仓库相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field, field_validator, HttpUrl


class RepositoryBase(BaseModel):
    """仓库基础 Schema"""
    type: str = Field(..., pattern=r"^(GITHUB|GITLAB|github|gitlab)$")
    owner: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    branch: str = Field(default="main", pattern=r"^[a-zA-Z0-9_-]+$")

    @field_validator('type')
    @classmethod
    def uppercase_type(cls, v: str) -> str:
        """将类型转换为大写"""
        return v.upper()


class RepositoryCreate(RepositoryBase):
    """创建仓库 Schema"""
    gitlab_url: str | None = Field(None, description="Required for GitLab repositories")
    access_token: str | None = Field(default=None, max_length=255)

    @field_validator('gitlab_url')
    @classmethod
    def validate_gitlab_url(cls, v: str | None, info) -> str | None:
        """GitLab 仓库需要配置 gitlab_url"""
        if info.data.get('type') == 'GITLAB' and not v:
            raise ValueError('gitlab_url is required for GitLab repositories')
        return v


class RepositoryUpdate(BaseModel):
    """更新仓库 Schema"""
    branch: str | None = Field(None, pattern=r"^[a-zA-Z0-9_-]+$")
    access_token: str | None = Field(default=None, max_length=255)
    webhook_secret: str | None = Field(default=None, max_length=255)
    webhook_enabled: bool | None = None
    enabled: bool | None = None
    gitlab_url: str | None = Field(None, max_length=500)


class RepositoryResponse(RepositoryBase):
    """仓库响应 Schema"""
    id: int
    gitlab_url: str | None
    webhook_enabled: bool
    enabled: bool
    last_sync_at: str | None
    created_at: str
    has_token: bool
    has_webhook_secret: bool
    skill_count: int = 0

    class Config:
        from_attributes = True


class WebhookConfig(BaseModel):
    """Webhook 配置 Schema"""
    enabled: bool
    secret: str | None = None


class SyncResponse(BaseModel):
    """同步响应 Schema"""
    status: str
    skills_added: int
    skills_updated: int
    skills_removed: int
    message: str
