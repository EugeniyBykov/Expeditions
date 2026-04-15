from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.constants import MIN_EXPEDITION_MEMBERS_COUNT
from app.db import AsyncUnitOfWork
from app.dto.expedition import ExpeditionCreateRequest, ExpeditionInviteRequest
from app.models import Expedition, User
from app.models.base import ExpeditionMemberState, ExpeditionStatus, UserRole
from app.repositories.expedition import ExpeditionRepository
from app.repositories.expedition_member import ExpeditionMemberRepository

from app.websockets.broadcast import (
    broadcast_expedition_status,
    broadcast_member_confirmed,
    broadcast_member_invited,
)


class ExpeditionService:
    def __init__(self) -> None:
        self.repository = ExpeditionRepository()
        self.member_repository = ExpeditionMemberRepository()

    async def _get_expedition_or_404(
        self,
        expedition_id: UUID,
        uow: AsyncUnitOfWork,
        for_update: bool = False,
    ) -> Expedition:
        if for_update:
            expedition = await self.repository.get_by_id_for_update(
                uow.session, expedition_id
            )
        else:
            expedition = await self.repository.get_by_id(uow.session, expedition_id)

        if expedition is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Expedition not found",
            )
        return expedition

    async def _get_user_or_404(
        self,
        user_id: UUID,
        uow: AsyncUnitOfWork,
    ) -> User:
        user = await uow.session.get(User, user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    def _ensure_chief_can_manage(
        self,
        expedition: Expedition,
        user: User,
    ) -> None:
        if user.role != UserRole.CHIEF or expedition.chief_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only expedition chief can change expedition status",
            )

    def _ensure_status_allowed(
        self,
        expedition: Expedition,
        allowed_statuses: tuple[ExpeditionStatus, ...],
        error_message: str,
    ) -> None:
        if expedition.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_message,
            )

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

    async def mark_ready(
        self,
        expedition_id: UUID,
        user: User,
        uow: AsyncUnitOfWork,
    ) -> Expedition:
        expedition = await self._get_expedition_or_404(expedition_id, uow, True)
        self._ensure_chief_can_manage(expedition, user)

        self._ensure_status_allowed(
            expedition,
            (ExpeditionStatus.DRAFT,),
            "Expedition can be moved to ready only from draft",
        )

        expedition.status = ExpeditionStatus.READY
        exp_id, status_val = expedition.id, expedition.status.value
        uow.after_commit(lambda: broadcast_expedition_status(exp_id, status_val))
        return expedition

    async def mark_active(
        self,
        expedition_id: UUID,
        user: User,
        uow: AsyncUnitOfWork,
    ) -> Expedition:
        expedition = await self._get_expedition_or_404(expedition_id, uow, True)
        self._ensure_chief_can_manage(expedition, user)

        self._ensure_status_allowed(
            expedition,
            (ExpeditionStatus.READY,),
            "Expedition can be moved to active only from ready",
        )

        now = datetime.now(timezone.utc)
        if expedition.start_at > now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expedition can be started only when start_at is reached",
            )

        confirmed_member_ids = await self.member_repository.get_confirmed_member_ids(
            uow.session,
            expedition.id,
        )

        if len(confirmed_member_ids) < MIN_EXPEDITION_MEMBERS_COUNT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"At least {MIN_EXPEDITION_MEMBERS_COUNT} confirmed members are required",
            )

        if len(confirmed_member_ids) > expedition.capacity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmed members exceed expedition capacity",
            )

        active_conflicts = (
            await self.member_repository.count_active_expeditions_for_users(
                uow.session,
                confirmed_member_ids,
                expedition.id,
            )
        )
        if active_conflicts > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more confirmed members are already in another active expedition",
            )

        expedition.status = ExpeditionStatus.ACTIVE
        exp_id, status_val = expedition.id, expedition.status.value
        uow.after_commit(lambda: broadcast_expedition_status(exp_id, status_val))
        return expedition

    async def mark_finished(
        self,
        expedition_id: UUID,
        user: User,
        uow: AsyncUnitOfWork,
    ) -> Expedition:
        expedition = await self._get_expedition_or_404(expedition_id, uow, True)
        self._ensure_chief_can_manage(expedition, user)

        self._ensure_status_allowed(
            expedition,
            (ExpeditionStatus.ACTIVE,),
            "Expedition can be finished only from active",
        )

        expedition.status = ExpeditionStatus.FINISHED
        exp_id, status_val = expedition.id, expedition.status.value
        uow.after_commit(lambda: broadcast_expedition_status(exp_id, status_val))
        return expedition

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

        if expedition.status != ExpeditionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft expeditions can be invited to",
            )

        invited_user = await self._get_user_or_404(payload.user_id, uow)

        if invited_user.role != UserRole.MEMBER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only users with member role can be invited",
            )

        invited_at = datetime.now(timezone.utc)

        try:
            member = await self.member_repository.create(
                uow.session,
                expedition_id=expedition.id,
                user_id=invited_user.id,
                invited_at=invited_at,
            )
            exp_id, user_id = expedition.id, invited_user.id
            uow.after_commit(
                lambda: broadcast_member_invited(exp_id, user_id, invited_at)
            )
            return member
        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already invited to this expedition",
            )

    async def confirm_invitation(
        self,
        expedition_id: UUID,
        user: User,
        uow: AsyncUnitOfWork,
    ):
        expedition = await self._get_expedition_or_404(expedition_id, uow)

        if expedition.status != ExpeditionStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only draft expeditions can be confirmed",
            )

        member = await self.member_repository.get_by_expedition_and_user(
            uow.session,
            expedition.id,
            user.id,
        )
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found",
            )

        if member.state != ExpeditionMemberState.INVITED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has already been confirmed",
            )

        member.state = ExpeditionMemberState.CONFIRMED
        member.confirmed_at = datetime.now(timezone.utc)

        exp_id, user_id, confirmed_at = expedition.id, user.id, member.confirmed_at
        uow.after_commit(
            lambda: broadcast_member_confirmed(exp_id, user_id, confirmed_at)
        )
        return member
