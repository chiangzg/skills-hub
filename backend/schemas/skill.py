"""
Skill 相关的 Pydantic Schema
"""
from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    """Skill 基础 Schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class SkillResponse(SkillBase):
    """Skill 响应 Schema"""
    id: int
    repository_id: int | None
    content: str | None = None
    directory: str
    repo_owner: str | None
    repo_name: str | None
    repo_branch: str | None
    readme_url: str | None
    raw_content_url: str | None
    stars: int
    views: int
    created_at: str
    updated_at: str
    categories: list[dict] = []
    repository: dict | None = None
    cli_command: str | None = None

    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """Skill 列表响应 Schema"""
    items: list[SkillResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class SkillSearchParams(BaseModel):
    """Skill 搜索参数 Schema"""
    keyword: str | None = None
    category_id: int | None = None
    repository_id: int | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at", pattern=r"^(created_at|updated_at|name|stars|views)$")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")


class SkillMetadata(BaseModel):
    """Skill 元数据 Schema（用于解析 SKILL.md）"""
    name: str | None = None
    description: str | None = None
    content: str | None = None
    directory: str | None = None
    tags: list[str] = []
