"""phase 7 extension save flow

Revision ID: 202605080003
Revises: 202605080002
Create Date: 2026-05-08 21:10:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605080003"
down_revision: str | None = "202605080002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "extension_save_events",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ingestion_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("platform", sa.String(length=40), nullable=False),
        sa.Column("source_type", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("page_title", sa.String(length=220), nullable=True),
        sa.Column("page_description", sa.String(length=500), nullable=True),
        sa.Column("browser", sa.String(length=40), nullable=True),
        sa.Column("extension_version", sa.String(length=40), nullable=True),
        sa.Column("page_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
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
            ["ingestion_job_id"],
            ["ingestion_jobs.id"],
            name=op.f("fk_extension_save_events_ingestion_job_id_ingestion_jobs"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_extension_save_events_source_id_sources"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_extension_save_events_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_extension_save_events_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_extension_save_events")),
    )
    op.create_index(
        "ix_extension_save_events_space_id",
        "extension_save_events",
        ["space_id"],
        unique=False,
    )
    op.create_index(
        "ix_extension_save_events_status",
        "extension_save_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_extension_save_events_user_created",
        "extension_save_events",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_extension_save_events_user_created", table_name="extension_save_events")
    op.drop_index("ix_extension_save_events_status", table_name="extension_save_events")
    op.drop_index("ix_extension_save_events_space_id", table_name="extension_save_events")
    op.drop_table("extension_save_events")