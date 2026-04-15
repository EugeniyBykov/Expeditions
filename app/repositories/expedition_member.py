from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models import ExpeditionMember, ExpeditionMemberState


class ExpeditionMemberRepository:
    async def get_by_expedition_and_user(
        self, session, expedition_id: UUID, user_id: UUID
    ) -> ExpeditionMember | None:
        result = await session.execute(
            select(ExpeditionMember).where(
                ExpeditionMember.expedition_id == expedition_id,
                ExpeditionMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        session,
        expedition_id: UUID,
        user_id: UUID,
        invited_at: datetime,
    ) -> ExpeditionMember:
        member = ExpeditionMember(
            expedition_id=expedition_id,
            user_id=user_id,
            state=ExpeditionMemberState.INVITED,
            invited_at=invited_at,
            confirmed_at=None,
        )
        session.add(member)
        await session.flush()
        await session.refresh(member)
        return member
