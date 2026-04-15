import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, AsyncMock

from app.main import app
from app.db import AsyncUnitOfWork, get_uow
from app.models.base import Base
from app.models.user import User
from app.security import create_access_token

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_engine):
    factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_uow():
        async with AsyncUnitOfWork(factory) as uow:
            yield uow

    app.dependency_overrides[get_uow] = override_get_uow

    with (
        patch(
            "app.services.expedition.broadcast_expedition_status",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.expedition.broadcast_member_invited", new_callable=AsyncMock
        ),
        patch(
            "app.services.expedition.broadcast_member_confirmed", new_callable=AsyncMock
        ),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


def auth_headers(user: User) -> dict:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}
