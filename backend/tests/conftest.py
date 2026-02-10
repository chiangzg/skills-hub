"""
Pytest 配置和共享 Fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from database import get_db, Base
from core import encryption
from models import User, Repository, Skill, Category, Webhook


# 测试数据库 URL (使用 SQLite 内存数据库)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """创建测试数据库引擎"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def test_encryption_key():
    """测试用加密密钥"""
    original_key = encryption._key
    encryption._key = b"test_encryption_key_32_bytes_long!"
    yield
    encryption._key = original_key


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录"""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def test_admin(test_db: AsyncSession) -> User:
    """创建测试管理员用户"""
    from core import password_manager

    admin = User(
        username="admin",
        password_hash=password_manager.hash_password("Admin@123"),
        email="admin@test.com",
        role=UserRole.ADMIN,
        is_active=True
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin


@pytest.fixture
async def test_user(test_db: AsyncSession) -> User:
    """创建测试普通用户"""
    from core import password_manager

    user = User(
        username="testuser",
        password_hash=password_manager.hash_password("Test@123"),
        email="user@test.com",
        role=UserRole.MAINTAINER,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def test_repository(test_db: AsyncSession, test_admin: User) -> Repository:
    """创建测试仓库"""
    repo = Repository(
        type=RepositoryType.GITHUB,
        owner="testowner",
        name="testrepo",
        branch="main",
        full_name="testowner/testrepo",
        webhook_enabled=False,
        last_sync_at=None
    )
    test_db.add(repo)
    await test_db.commit()
    await test_db.refresh(repo)
    return repo


@pytest.fixture
def sample_skill_md_content() -> str:
    """示例 SKILL.md 内容"""
    return '''---
name: "Test Skill"
description: "A test skill for unit testing"
tags: ["python", "testing"]
---

# Test Skill

This is a test skill content.
'''


@pytest.fixture
def sample_skill_file(temp_dir: Path, sample_skill_md_content: str) -> Path:
    """创建示例 SKILL.md 文件"""
    skill_file = temp_dir / "SKILL.md"
    skill_file.write_text(sample_skill_md_content, encoding="utf-8")
    return skill_file


# Pytest 配置
def pytest_configure(config):
    """Pytest 配置"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
