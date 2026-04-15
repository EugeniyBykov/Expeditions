from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, ExpeditionMemberState


class ExpeditionMember(Base):
    __tablename__ = "expedition_members"
    __table_args__ = (
        UniqueConstraint(
            "expedition_id", "user_id", name="expedition_member_user_id_expedition_id"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    expedition_id: Mapped[UUID] = mapped_column(
        ForeignKey("expeditions.id"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    state: Mapped[ExpeditionMemberState] = mapped_column(
        SAEnum(
            ExpeditionMemberState,
            name="expedition_member_state",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    invited_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    expedition = relationship("Expedition", back_populates="members")
    user = relationship("User", back_populates="expedition_memberships")
