"""Add servers table

Revision ID: 20260415_0002
Revises: 20260413_0001
Create Date: 2026-04-15 09:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260415_0002"
down_revision = "20260413_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("servers"):
        return

    op.create_table(
        "servers",
        sa.Column("UUID", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("server_name", sa.String(length=120), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column(
            "accessLevel",
            postgresql.ENUM("audio", "video", "blast_dial", name="accesslevel", create_type=False),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("UUID"),
    )
    op.create_index("ix_servers_UUID", "servers", ["UUID"], unique=False)
    op.create_index("ix_servers_accessLevel", "servers", ["accessLevel"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("servers"):
        op.drop_index("ix_servers_accessLevel", table_name="servers")
        op.drop_index("ix_servers_UUID", table_name="servers")
        op.drop_table("servers")