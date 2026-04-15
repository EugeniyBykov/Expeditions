from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UserRole(str, Enum):
    CHIEF = "chief"
    MEMBER = "member"


class ExpeditionStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    ACTIVE = "active"
    FINISHED = "finished"


class ExpeditionMemberState(str, Enum):
    INVITED = "invited"
    CONFIRMED = "confirmed"
