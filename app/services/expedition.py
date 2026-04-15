from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.db import AsyncUnitOfWork
from app.dto.expedition import ExpeditionCreateRequest, ExpeditionInviteRequest
from app.models import Expedition, User
from app.models.base import ExpeditionStatus, UserRole
from app.repositories.expedition import ExpeditionRepository
from app.repositories.expedition_member import ExpeditionMemberRepository


class ExpeditionService:
    def __init__(self) -> None:
        self.repository = ExpeditionRepository()
        self.member_repository = ExpeditionMemberRepository()

    async def create_expedition(
        self,
        payload: ExpeditionCreateRequest,
        user: User,
        uow: AsyncUnitOfWork,
    ) -> Expedition:
        if user.role != UserRole.CHIEF:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only chiefs can create expeditions",
            )

        expedition = Expedition(
            title=payload.title,
            description=payload.description,
            status=ExpeditionStatus.DRAFT,
            start_at=payload.start_at,
            end_at=payload.end_at,
            capacity=payload.capacity,
            chief_id=user.id,
        )
        return await self.repository.create(uow.session, expedition)

    async def invite_member(
        self,
        payload: ExpeditionInviteRequest,
        user: User,
        uow: AsyncUnitOfWork,
    ):
        expedition = await self._get_expedition_or_404(payload.expedition_id, uow)

        if expedition.chief_id != user.id or user.role != UserRole.CHIEF:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expedition chief can invite members",
            )

        invited_user = await self._get_user_or_404(payload.user_id, uow)

        if invited_user.role != UserRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only users with member role can be invited",
            )

        invited_at = datetime.now(timezone.utc)

        try:
            return await self.member_repository.create(
                uow.session,
                expedition_id=expedition.id,
                user_id=invited_user.id,
                invited_at=invited_at,
            )
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already invited to this expedition",
            )

    async def _get_expedition_or_404(
        self,
        expedition_id,
        uow: AsyncUnitOfWork,
    ) -> Expedition:
        expedition = await self.repository.get_by_id(uow.session, expedition_id)
        if expedition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expedition not found",
            )
        return expedition

    async def _get_user_or_404(
        self,
        user_id,
        uow: AsyncUnitOfWork,
    ) -> User:
        user = await uow.session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
