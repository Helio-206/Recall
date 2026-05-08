"""phase 3 transcripts

Revision ID: 202605070002
Revises: 202605070001
Create Date: 2026-05-07 00:02:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605070002"
down_revision: str | None = "202605070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transcript_jobs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
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
            name=op.f("fk_transcript_jobs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_transcript_jobs_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript_jobs")),
    )
    op.create_index("ix_transcript_jobs_status", "transcript_jobs", ["status"], unique=False)
    op.create_index("ix_transcript_jobs_user_id", "transcript_jobs", ["user_id"], unique=False)
    op.create_index("ix_transcript_jobs_video_id", "transcript_jobs", ["video_id"], unique=False)

    op.create_table(
        "transcript_segments",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.Float(), nullable=False),
        sa.Column("end_time", sa.Float(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
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
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_transcript_segments_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_transcript_segments")),
    )
    op.create_index(
        "ix_transcript_segments_video_order",
        "transcript_segments",
        ["video_id", "order_index"],
        unique=False,
    )
    op.create_index(
        "ix_transcript_segments_video_start",
        "transcript_segments",
        ["video_id", "start_time"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_transcript_segments_video_start", table_name="transcript_segments")
    op.drop_index("ix_transcript_segments_video_order", table_name="transcript_segments")
    op.drop_table("transcript_segments")
    op.drop_index("ix_transcript_jobs_video_id", table_name="transcript_jobs")
    op.drop_index("ix_transcript_jobs_user_id", table_name="transcript_jobs")
    op.drop_index("ix_transcript_jobs_status", table_name="transcript_jobs")
    op.drop_table("transcript_jobs")
