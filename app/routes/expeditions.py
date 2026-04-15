from fastapi import APIRouter, Depends, status

from app.db import AsyncUnitOfWork, get_uow
from app.models import User
from app.security import get_current_user
from app.services.expedition import (
    ExpeditionCreateRequest,
    ExpeditionResponse,
    ExpeditionService,
)

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
