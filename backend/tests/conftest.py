"""pytest 全局夹具：SQLite 内存测试库 + 依赖覆盖，不触碰真实 MySQL / embedding 模型。

注意：database.engine 指向真实 MySQL，但 create_async_engine 是惰性的，
导入阶段不会建立连接；测试统一走下方独立的 SQLite 测试引擎。
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture
async def engine():
    """独立测试引擎：StaticPool 单连接共享内存 SQLite。"""
    test_engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine
    await test_engine.dispose()


@pytest.fixture
async def db_session(engine):
    """供服务层测试直接注入的会话。"""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest.fixture
async def client(engine):
    """ASGI 测试客户端：把 get_db 依赖覆盖到测试引擎。"""
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
