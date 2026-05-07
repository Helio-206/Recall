"""phase 2 ingestion

Revision ID: 202605070001
Revises: 202605060001
Create Date: 2026-05-07 00:01:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605070001"
down_revision: str | None = "202605060001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("author", sa.String(length=180), nullable=True),
        sa.Column("thumbnail", sa.Text(), nullable=True),
        sa.Column("duration", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
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
            name=op.f("fk_sources_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_sources_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
    )
    op.create_index("ix_sources_space_id", "sources", ["space_id"], unique=False)
    op.create_index("ix_sources_status", "sources", ["status"], unique=False)
    op.create_index("ix_sources_user_id", "sources", ["user_id"], unique=False)

    op.create_table(
        "ingestion_jobs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_ingestion_jobs_source_id_sources"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_ingestion_jobs_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_ingestion_jobs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ingestion_jobs")),
    )
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"], unique=False)
    op.create_index("ix_ingestion_jobs_user_id", "ingestion_jobs", ["user_id"], unique=False)

    op.add_column("videos", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "videos",
        sa.Column(
            "metadata_status",
            sa.String(length=40),
            server_default="completed",
            nullable=False,
        ),
    )
    op.add_column(
        "videos",
        sa.Column(
            "transcript_status",
            sa.String(length=40),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "videos",
        sa.Column(
            "processing_status",
            sa.String(length=40),
            server_default="completed",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        op.f("fk_videos_source_id_sources"),
        "videos",
        "sources",
        ["source_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(op.f("uq_videos_space_url"), "videos", ["space_id", "url"])
    op.create_index("ix_videos_source_id", "videos", ["source_id"], unique=False)
    op.create_index("ix_videos_url", "videos", ["url"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_videos_url", table_name="videos")
    op.drop_index("ix_videos_source_id", table_name="videos")
    op.drop_constraint(op.f("uq_videos_space_url"), "videos", type_="unique")
    op.drop_constraint(op.f("fk_videos_source_id_sources"), "videos", type_="foreignkey")
    op.drop_column("videos", "processing_status")
    op.drop_column("videos", "transcript_status")
    op.drop_column("videos", "metadata_status")
    op.drop_column("videos", "source_id")
    op.drop_index("ix_ingestion_jobs_user_id", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_status", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    op.drop_index("ix_sources_user_id", table_name="sources")
    op.drop_index("ix_sources_status", table_name="sources")
    op.drop_index("ix_sources_space_id", table_name="sources")
    op.drop_table("sources")
