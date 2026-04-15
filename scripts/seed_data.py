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
MEMBER_COUNT = 20


def build_chief_email(index: int) -> str:
    return f"chief{index}@test.com"


def build_member_email(index: int) -> str:
    return f"member{index}@test.com"


async def get_existing_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def seed_chiefs(session: AsyncSession) -> list[User]:
    chiefs: list[User] = []

    for i in range(1, CHIEF_COUNT + 1):
        email = build_chief_email(i)
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


async def seed_members(session: AsyncSession) -> list[User]:
    members: list[User] = []

    for i in range(1, MEMBER_COUNT + 1):
        email = build_member_email(i)
        user = await get_existing_user_by_email(session, email)
        if user is None:
            user = User(
                id=uuid4(),
                email=email,
                name=f"Member {i}",
                role=UserRole.MEMBER,
            )
            session.add(user)
        members.append(user)

    await session.flush()
    return members


async def main() -> None:
    async with async_session_factory() as session:
        async with session.begin():
            await seed_chiefs(session)
            await seed_members(session)

    print("Seed chiefs and members have been created successfully.")


if __name__ == "__main__":
    asyncio.run(main())