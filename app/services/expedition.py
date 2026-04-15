from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.db import AsyncUnitOfWork
from app.models import Expedition, User
from app.models.base import ExpeditionStatus, UserRole
from app.repositories.expedition import ExpeditionRepository


class ExpeditionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    start_at: datetime
    end_at: datetime | None = None
    capacity: int = Field(ge=2)

    @model_validator(mode="after")
    def validate_end_at(self) -> "ExpeditionCreateRequest":
        if self.end_at is not None and self.end_at <= self.start_at:
            raise ValueError("end_at must be greater than start_at")
        return self


class ExpeditionResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: ExpeditionStatus
    start_at: datetime
    end_at: datetime | None
    capacity: int
    chief_id: UUID

    model_config = {"from_attributes": True}


class ExpeditionService:
    def __init__(self) -> None:
        self.repository = ExpeditionRepository()

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

        if uow.session is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database session is not initialized",
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
