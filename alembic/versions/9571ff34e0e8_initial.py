"""initial

Revision ID: 9571ff34e0e8
Revises: 
Create Date: 2026-04-15 00:05:33.091166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "9571ff34e0e8"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


user_role_enum = postgresql.ENUM("chief", "member", name="user_role", create_type=False)
expedition_status_enum = postgresql.ENUM(
    "draft", "ready", "active", "finished", name="expedition_status", create_type=False
)
expedition_member_state_enum = postgresql.ENUM(
    "invited", "confirmed", name="expedition_member_state", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()

    user_role_enum.create(bind, checkfirst=True)
    expedition_status_enum.create(bind, checkfirst=True)
    expedition_member_state_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "expeditions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", expedition_status_enum, nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("chief_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chief_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "expedition_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("expedition_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("state", expedition_member_state_enum, nullable=False),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["expedition_id"], ["expeditions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_unique_constraint(
        "expedition_member_user_id_expedition_id",
        "expedition_members",
        ["expedition_id", "user_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "expedition_member_user_id_expedition_id",
        "expedition_members",
        type_="unique",
    )

    op.drop_table("expedition_members")
    op.drop_table("expeditions")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    expedition_member_state_enum.drop(bind, checkfirst=True)
    expedition_status_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)

