from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.db import async_session_factory
from app.models import Expedition, ExpeditionMember
from app.websockets.manager import ws_manager
from app.websockets.schemas import WebSocketEvent, WebSocketEventType


async def _get_expedition_subscriber_ids(expedition_id: UUID) -> list[UUID]:
    async with async_session_factory() as session:
        chief_result = await session.execute(
            select(Expedition.chief_id).where(Expedition.id == expedition_id)
        )
        chief_id = chief_result.scalar_one_or_none()

        if chief_id is None:
            return []

        members_result = await session.execute(
            select(ExpeditionMember.user_id).where(
                ExpeditionMember.expedition_id == expedition_id
            )
        )
        member_ids = [row[0] for row in members_result.all()]

        return [chief_id, *member_ids]


async def broadcast_member_invited(
    expedition_id: UUID,
    user_id: UUID,
    invited_at,
) -> None:
    event = WebSocketEvent(
        type=WebSocketEventType.MEMBER_INVITED,
        expedition_id=expedition_id,
        data={
            "user_id": str(user_id),
            "invited_at": invited_at.isoformat(),
        },
    )
    subscriber_ids = await _get_expedition_subscriber_ids(expedition_id)
    await ws_manager.broadcast_to_users(
        [str(user_id) for user_id in subscriber_ids],
        event.model_dump(mode="json"),
    )


async def broadcast_member_confirmed(
    expedition_id: UUID,
    user_id: UUID,
    confirmed_at,
) -> None:
    event = WebSocketEvent(
        type=WebSocketEventType.MEMBER_CONFIRMED,
        expedition_id=expedition_id,
        data={
            "user_id": str(user_id),
            "confirmed_at": confirmed_at.isoformat(),
        },
    )
    subscriber_ids = await _get_expedition_subscriber_ids(expedition_id)
    await ws_manager.broadcast_to_users(
        [str(user_id) for user_id in subscriber_ids],
        event.model_dump(mode="json"),
    )


async def broadcast_expedition_status(
    expedition_id: UUID,
    status: str,
) -> None:
    event = WebSocketEvent(
        type=WebSocketEventType.EXPEDITION_STATUS,
        expedition_id=expedition_id,
        data={"status": status},
    )
    subscriber_ids = await _get_expedition_subscriber_ids(expedition_id)
    await ws_manager.broadcast_to_users(
        [str(user_id) for user_id in subscriber_ids],
        event.model_dump(mode="json"),
    )
