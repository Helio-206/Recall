"""phase 5 search notes

Revision ID: 202605080001
Revises: 202605070003
Create Date: 2026-05-08 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605080001"
down_revision: str | None = "202605070003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "video_notes",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("anchor_timestamp", sa.Float(), nullable=True),
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
            name=op.f("fk_video_notes_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_video_notes_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_video_notes")),
        sa.UniqueConstraint("user_id", "video_id", name=op.f("uq_video_notes_user_id")),
    )
    op.create_index("ix_video_notes_user_id", "video_notes", ["user_id"], unique=False)
    op.create_index("ix_video_notes_video_id", "video_notes", ["video_id"], unique=False)

    op.create_table(
        "search_queries",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.String(length=220), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("use_count", sa.Integer(), nullable=False),
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
            name=op.f("fk_search_queries_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_queries")),
        sa.UniqueConstraint("user_id", "query", name=op.f("uq_search_queries_user_id")),
    )
    op.create_index("ix_search_queries_user_id", "search_queries", ["user_id"], unique=False)
    op.create_index(
        "ix_search_queries_last_used_at",
        "search_queries",
        ["last_used_at"],
        unique=False,
    )

    op.create_table(
        "search_result_clicks",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.String(length=220), nullable=False),
        sa.Column("result_kind", sa.String(length=40), nullable=False),
        sa.Column("result_id", sa.String(length=120), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("timestamp", sa.Float(), nullable=True),
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
            name=op.f("fk_search_result_clicks_space_id_learning_spaces"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_search_result_clicks_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_search_result_clicks_video_id_videos"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_search_result_clicks")),
    )
    op.create_index(
        "ix_search_result_clicks_user_id",
        "search_result_clicks",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_search_result_clicks_result_kind",
        "search_result_clicks",
        ["result_kind"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_search_result_clicks_result_kind", table_name="search_result_clicks")
    op.drop_index("ix_search_result_clicks_user_id", table_name="search_result_clicks")
    op.drop_table("search_result_clicks")
    op.drop_index("ix_search_queries_last_used_at", table_name="search_queries")
    op.drop_index("ix_search_queries_user_id", table_name="search_queries")
    op.drop_table("search_queries")
    op.drop_index("ix_video_notes_video_id", table_name="video_notes")
    op.drop_index("ix_video_notes_user_id", table_name="video_notes")
    op.drop_table("video_notes")