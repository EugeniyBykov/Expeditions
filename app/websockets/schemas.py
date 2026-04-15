from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class WebSocketEventType(str, Enum):
    MEMBER_INVITED = "member_invited"
    MEMBER_CONFIRMED = "member_confirmed"
    EXPEDITION_STATUS = "expedition_status"


class WebSocketEvent(BaseModel):
    type: WebSocketEventType
    expedition_id: UUID
    data: dict


class MemberInvitedData(BaseModel):
    user_id: UUID
    invited_at: datetime


class MemberConfirmedData(BaseModel):
    user_id: UUID
    confirmed_at: datetime


class ExpeditionStatusData(BaseModel):
    status: str
