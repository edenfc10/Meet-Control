"""Add meeting_participant_status table

Revision ID: 20260615_0003
Revises: 20260415_0002
Create Date: 2026-06-15 09:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260615_0003"
down_revision = "20260415_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("meeting_participant_status"):
        return

    op.create_table(
        "meeting_participant_status",
        sa.Column("meeting_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_uuid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_kicked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(["meeting_uuid"], ["meetings.UUID"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_uuid"], ["users.UUID"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("meeting_uuid", "user_uuid"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("meeting_participant_status"):
        op.drop_table("meeting_participant_status")
