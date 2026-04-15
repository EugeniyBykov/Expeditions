from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.db import AsyncUnitOfWork, get_uow
from app.models import User
from app.security import get_current_user
from app.dto.expedition import (
    ExpeditionCreateRequest,
    ExpeditionResponse,
    ExpeditionInviteResponse,
    ExpeditionInviteRequest,
)
from app.services.expedition import ExpeditionService

router = APIRouter(prefix="", tags=["expeditions"])


@router.post(
    "",
    response_model=ExpeditionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_expedition(
    payload: ExpeditionCreateRequest,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionResponse:
    service = ExpeditionService()
    expedition = await service.create_expedition(payload, current_user, uow)
    return ExpeditionResponse.model_validate(expedition)


@router.post(
    "/{expedition_id}/ready",
    response_model=ExpeditionResponse,
)
async def mark_ready(
    expedition_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionResponse:
    service = ExpeditionService()
    expedition = await service.mark_ready(expedition_id, current_user, uow)
    return ExpeditionResponse.model_validate(expedition)


@router.post(
    "/{expedition_id}/active",
    response_model=ExpeditionResponse,
)
async def mark_active(
    expedition_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionResponse:
    service = ExpeditionService()
    expedition = await service.mark_active(expedition_id, current_user, uow)
    return ExpeditionResponse.model_validate(expedition)


@router.post(
    "/{expedition_id}/finished",
    response_model=ExpeditionResponse,
)
async def mark_finished(
    expedition_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionResponse:
    service = ExpeditionService()
    expedition = await service.mark_finished(expedition_id, current_user, uow)
    return ExpeditionResponse.model_validate(expedition)


@router.post(
    "/invite",
    response_model=ExpeditionInviteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_member(
    payload: ExpeditionInviteRequest,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionInviteResponse:
    service = ExpeditionService()
    member = await service.invite_member(payload, current_user, uow)
    return ExpeditionInviteResponse.model_validate(member)


@router.post(
    "/invite/confirm/{expedition_id}",
    response_model=ExpeditionInviteResponse,
)
async def confirm_invitation(
    expedition_id: UUID,
    current_user: User = Depends(get_current_user),
    uow: AsyncUnitOfWork = Depends(get_uow),
) -> ExpeditionInviteResponse:
    service = ExpeditionService()
    member = await service.confirm_invitation(expedition_id, current_user, uow)
    return ExpeditionInviteResponse.model_validate(member)
