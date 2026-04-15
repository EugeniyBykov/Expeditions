from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.models.base import ExpeditionStatus


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


class ExpeditionInviteRequest(BaseModel):
    expedition_id: UUID
    user_id: UUID


class ExpeditionInviteResponse(BaseModel):
    id: UUID
    expedition_id: UUID
    user_id: UUID
    state: str
    invited_at: datetime
    confirmed_at: datetime | None

    model_config = {"from_attributes": True}
