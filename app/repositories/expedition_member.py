from datetime import datetime
from uuid import UUID

from sqlalchemy import select

from app.models import (
    Expedition,
    ExpeditionMember,
    ExpeditionMemberState,
    ExpeditionStatus,
)


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

    async def update(self, session, member: ExpeditionMember) -> ExpeditionMember:
        await session.flush()
        await session.refresh(member)
        return member

    async def get_confirmed_member_ids(
        self, session, expedition_id: UUID
    ) -> list[UUID]:
        result = await session.execute(
            select(ExpeditionMember.user_id).where(
                ExpeditionMember.expedition_id == expedition_id,
                ExpeditionMember.state == ExpeditionMemberState.CONFIRMED,
            )
        )
        return [row[0] for row in result.all()]

    async def count_active_expeditions_for_users(
        self,
        session,
        user_ids: list[UUID],
        exclude_expedition_id: UUID,
    ) -> int:
        if not user_ids:
            return 0

        result = await session.execute(
            select(ExpeditionMember)
            .join(ExpeditionMember.expedition)
            .where(
                ExpeditionMember.user_id.in_(user_ids),
                ExpeditionMember.state == ExpeditionMemberState.CONFIRMED,
                Expedition.id != exclude_expedition_id,
                Expedition.status == ExpeditionStatus.ACTIVE,
            )
        )
        return len(result.scalars().all())
