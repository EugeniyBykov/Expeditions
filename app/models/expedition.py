from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, ExpeditionStatus


class Expedition(Base, TimestampMixin):
    __tablename__ = "expeditions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ExpeditionStatus] = mapped_column(
        SAEnum(
            ExpeditionStatus,
            name="expedition_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)

    chief_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    chief = relationship(
        "User",
        back_populates="chief_expeditions",
        foreign_keys=[chief_id],
    )
    members = relationship(
        "ExpeditionMember",
        back_populates="expedition",
        cascade="all, delete-orphan",
    )
