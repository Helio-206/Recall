"""initial schema

Revision ID: 202605060001
Revises:
Create Date: 2026-05-06 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605060001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "learning_spaces",
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("topic", sa.String(length=120), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_learning_spaces_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_spaces")),
    )
    op.create_index(
        "ix_learning_spaces_user_created",
        "learning_spaces",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_learning_spaces_user_topic",
        "learning_spaces",
        ["user_id", "topic"],
        unique=False,
    )

    op.create_table(
        "videos",
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("thumbnail", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=160), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_videos_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_videos")),
    )
    op.create_index("ix_videos_space_completed", "videos", ["space_id", "completed"], unique=False)
    op.create_index("ix_videos_space_order", "videos", ["space_id", "order_index"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_videos_space_order", table_name="videos")
    op.drop_index("ix_videos_space_completed", table_name="videos")
    op.drop_table("videos")
    op.drop_index("ix_learning_spaces_user_topic", table_name="learning_spaces")
    op.drop_index("ix_learning_spaces_user_created", table_name="learning_spaces")
    op.drop_table("learning_spaces")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
