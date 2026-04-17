"""Initial schema

Revision ID: 20260413_0001
Revises:
Create Date: 2026-04-13 22:20:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql


revision = "20260413_0001"
down_revision = None
branch_labels = None
depends_on = None


def _create_enum(name: str, values: list[str]) -> None:
    quoted_values = ", ".join(f"'{value}'" for value in values)
    op.execute(
        sa.text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                    CREATE TYPE {name} AS ENUM ({quoted_values});
                END IF;
            END
            $$;
            """
        )
    )


def _create_indexes() -> None:
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_groups_UUID ON groups (\"UUID\")"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_meetings_UUID ON meetings (\"UUID\")"))
    op.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_meetings_m_number ON meetings (m_number)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_used_refresh_tokens_jti ON used_refresh_tokens (jti)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_used_refresh_tokens_user_uuid ON used_refresh_tokens (user_uuid)"))
    op.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_s_id ON users (s_id)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_users_UUID ON users (\"UUID\")"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_favorite_meetings_UUID ON favorite_meetings (\"UUID\")"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_favorite_meetings_member_uuid ON favorite_meetings (member_uuid)"))
    op.execute(sa.text("CREATE INDEX IF NOT EXISTS ix_favorite_meetings_meeting_uuid ON favorite_meetings (meeting_uuid)"))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    _create_enum("accesslevel", ["audio", "video", "blast_dial"])
    _create_enum("membergroupaccesslevel", ["audio", "video", "blast_dial"])
    _create_enum("userrole", ["super_admin", "admin", "agent", "viewer"])

    if not inspector.has_table("groups"):
        op.create_table(
            "groups",
            sa.Column("UUID", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("name", sa.String(length=50), nullable=False),
            sa.PrimaryKeyConstraint("UUID"),
        )

    if not inspector.has_table("users"):
        op.create_table(
            "users",
            sa.Column("UUID", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("s_id", sa.String(length=50), nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("password", sa.String(length=250), nullable=False),
            sa.Column(
                "role",
                postgresql.ENUM("super_admin", "admin", "agent", "viewer", name="userrole", create_type=False),
                nullable=False,
            ),
            sa.PrimaryKeyConstraint("UUID"),
            sa.UniqueConstraint("s_id"),
        )

    if not inspector.has_table("meetings"):
        op.create_table(
            "meetings",
            sa.Column("UUID", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("m_number", sa.String(length=15), nullable=False),
            sa.Column(
                "accessLevel",
                postgresql.ENUM("audio", "video", "blast_dial", name="accesslevel", create_type=False),
                nullable=False,
            ),
            sa.Column("password", sa.String(length=120), nullable=True),
            sa.PrimaryKeyConstraint("UUID"),
            sa.UniqueConstraint("m_number"),
        )
    else:
        meeting_columns = {column["name"] for column in inspector.get_columns("meetings")}
        if "password" not in meeting_columns:
            op.add_column("meetings", sa.Column("password", sa.String(length=120), nullable=True))

    if not inspector.has_table("meeting_group_association"):
        op.create_table(
            "meeting_group_association",
            sa.Column("meeting_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["group_id"], ["groups.UUID"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["meeting_id"], ["meetings.UUID"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("meeting_id", "group_id"),
        )

    if not inspector.has_table("member_group_access"):
        op.create_table(
            "member_group_access",
            sa.Column("member_uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("group_uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column(
                "access_level",
                postgresql.ENUM("audio", "video", "blast_dial", name="membergroupaccesslevel", create_type=False),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["group_uuid"], ["groups.UUID"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_uuid"], ["users.UUID"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("member_uuid", "group_uuid", "access_level"),
        )

    if not inspector.has_table("used_refresh_tokens"):
        op.create_table(
            "used_refresh_tokens",
            sa.Column("jti", sa.String(), nullable=False),
            sa.Column("user_uuid", sa.String(), nullable=True),
            sa.Column("expires_at", sa.Integer(), nullable=True),
            sa.PrimaryKeyConstraint("jti"),
        )

    if not inspector.has_table("favorite_meetings"):
        op.create_table(
            "favorite_meetings",
            sa.Column("UUID", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("member_uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("meeting_uuid", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["meeting_uuid"], ["meetings.UUID"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_uuid"], ["users.UUID"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("UUID"),
            sa.UniqueConstraint("member_uuid", "meeting_uuid", name="uq_favorite_member_meeting"),
        )

    _create_indexes()


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("favorite_meetings"):
        op.drop_table("favorite_meetings")
    if inspector.has_table("used_refresh_tokens"):
        op.drop_table("used_refresh_tokens")
    if inspector.has_table("member_group_access"):
        op.drop_table("member_group_access")
    if inspector.has_table("meeting_group_association"):
        op.drop_table("meeting_group_association")
    if inspector.has_table("meetings"):
        op.drop_table("meetings")
    if inspector.has_table("users"):
        op.drop_table("users")
    if inspector.has_table("groups"):
        op.drop_table("groups")

    op.execute(sa.text("DROP TYPE IF EXISTS membergroupaccesslevel"))
    op.execute(sa.text("DROP TYPE IF EXISTS accesslevel"))
    op.execute(sa.text("DROP TYPE IF EXISTS userrole"))