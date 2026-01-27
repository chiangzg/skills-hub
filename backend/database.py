"""
数据库配置模块
使用 SQLAlchemy + aiomysql 实现异步 MySQL 连接
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+aiomysql://root:password@localhost:3306/skills"
)

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 生产环境设置为 False
    pool_pre_ping=True,  # 连接健康检查
    pool_size=10,  # 连接池大小
    max_overflow=20,  # 最大溢出连接数
)

# 创建会话工厂
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 声明式基类
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    依赖注入：获取数据库会话
    用于 FastAPI 依赖注入
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    初始化数据库连接
    用于应用启动时测试连接
    """
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
