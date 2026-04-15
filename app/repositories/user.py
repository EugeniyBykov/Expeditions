from __future__ import annotations

from sqlalchemy import select

from app.models import User


class UserRepository:
    async def get_by_email(self, session, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, session, user_id) -> User | None:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
