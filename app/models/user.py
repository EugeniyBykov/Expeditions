from uuid import UUID, uuid4

from sqlalchemy import String, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    chief_expeditions = relationship(
        "Expedition",
        back_populates="chief",
        foreign_keys="Expedition.chief_id",
    )
    expedition_memberships = relationship(
        "ExpeditionMember",
        back_populates="user",
        foreign_keys="ExpeditionMember.user_id",
    )
