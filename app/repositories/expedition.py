from __future__ import annotations

from app.models import Expedition

from uuid import UUID
from sqlalchemy import select


class ExpeditionRepository:
    async def create(self, session, expedition: Expedition) -> Expedition:
        session.add(expedition)
        await session.flush()
        await session.refresh(expedition)
        return expedition

    async def get_by_id(self, session, expedition_id: UUID) -> Expedition | None:
        result = await session.execute(
            select(Expedition).where(Expedition.id == expedition_id)
        )
        return result.scalar_one_or_none()
