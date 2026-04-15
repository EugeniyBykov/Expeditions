from __future__ import annotations

import asyncio
import os
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.db import async_session_factory
    from app.models import User
    from app.models.base import UserRole
except ModuleNotFoundError:
    import sys

    sys.path.append(os.getcwd())

    from app.db import async_session_factory
    from app.models import User
    from app.models.base import UserRole


CHIEF_COUNT = 3


def build_email(index: int) -> str:
    return f"chief{index}@test.test"


async def get_existing_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def seed_chiefs(session: AsyncSession) -> list[User]:
    chiefs: list[User] = []

    for i in range(1, CHIEF_COUNT + 1):
        email = build_email(i)
        user = await get_existing_user_by_email(session, email)
        if user is None:
            user = User(
                id=uuid4(),
                email=email,
                name=f"Chief {i}",
                role=UserRole.CHIEF,
            )
            session.add(user)
        chiefs.append(user)

    await session.flush()
    return chiefs


async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            await seed_chiefs(session)

    print("Seed chiefs have been created successfully.")


if __name__ == "__main__":
    asyncio.run(main())