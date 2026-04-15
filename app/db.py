from __future__ import annotations

from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import AbstractAsyncContextManager
from typing import Any, Optional, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.settings import database_settings

engine = create_async_engine(
    database_settings.sqlalchemy_url,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

T = TypeVar("T")


class AsyncUnitOfWork(AbstractAsyncContextManager["AsyncUnitOfWork"]):
    """Async Unit of Work for managing a database transaction lifecycle."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] = async_session_factory
    ):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None
        self._post_commit: list[Callable[[], Coroutine[Any, Any, None]]] = []

    def after_commit(self, coro_fn: Callable[[], Coroutine[Any, Any, None]]) -> None:
        """Register a coroutine function to be called after a successful commit."""
        self._post_commit.append(coro_fn)

    async def _run_post_commit(self) -> None:
        callbacks, self._post_commit = self._post_commit, []
        for cb in callbacks:
            await cb()

    async def __aenter__(self) -> "AsyncUnitOfWork":
        self.session = self._session_factory()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if self.session is None:
            return

        try:
            if exc_type is None:
                await self.session.commit()
                await self._run_post_commit()
            else:
                await self.session.rollback()
        finally:
            await self.session.close()

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        await self.session.commit()
        await self._run_post_commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        await self.session.rollback()


async def get_uow() -> AsyncGenerator[AsyncUnitOfWork, None]:
    async with AsyncUnitOfWork() as uow:
        yield uow
