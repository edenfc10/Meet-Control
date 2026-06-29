"""Add port column to servers table

Revision ID: 20260629_0004
Revises: 20260615_0003
Create Date: 2026-06-29 09:50:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "20260629_0004"
down_revision = "20260615_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    columns = [col["name"] for col in inspector.get_columns("servers")]
    if "port" in columns:
        return

    op.add_column("servers", sa.Column("port", sa.Integer(), nullable=False, server_default="0"))
    op.alter_column("servers", "port", server_default=None)


def downgrade() -> None:
    op.drop_column("servers", "port")
