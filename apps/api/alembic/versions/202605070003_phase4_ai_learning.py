"""phase 4 ai learning

Revision ID: 202605070003
Revises: 202605070002
Create Date: 2026-05-07 00:03:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605070003"
down_revision: str | None = "202605070002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_summary_jobs",
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
            name=op.f("fk_ai_summary_jobs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_ai_summary_jobs_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_summary_jobs")),
    )
    op.create_index("ix_ai_summary_jobs_status", "ai_summary_jobs", ["status"], unique=False)
    op.create_index("ix_ai_summary_jobs_user_id", "ai_summary_jobs", ["user_id"], unique=False)
    op.create_index("ix_ai_summary_jobs_video_id", "ai_summary_jobs", ["video_id"], unique=False)

    op.create_table(
        "ai_summaries",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=True),
        sa.Column("detailed_summary", sa.Text(), nullable=True),
        sa.Column("learning_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
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
            name=op.f("fk_ai_summaries_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_summaries")),
        sa.UniqueConstraint("video_id", name=op.f("uq_ai_summaries_video_id")),
    )
    op.create_index("ix_ai_summaries_status", "ai_summaries", ["status"], unique=False)

    op.create_table(
        "key_concepts",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept", sa.String(length=220), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_key_concepts_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_key_concepts")),
    )
    op.create_index("ix_key_concepts_video_id", "key_concepts", ["video_id"], unique=False)

    op.create_table(
        "key_takeaways",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_key_takeaways_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_key_takeaways")),
    )
    op.create_index("ix_key_takeaways_video_id", "key_takeaways", ["video_id"], unique=False)

    op.create_table(
        "review_questions",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_review_questions_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_review_questions")),
    )
    op.create_index(
        "ix_review_questions_video_id",
        "review_questions",
        ["video_id"],
        unique=False,
    )

    op.create_table(
        "important_moments",
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=220), nullable=False),
        sa.Column("timestamp", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_important_moments_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_important_moments")),
    )
    op.create_index(
        "ix_important_moments_video_timestamp",
        "important_moments",
        ["video_id", "timestamp"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_important_moments_video_timestamp", table_name="important_moments")
    op.drop_table("important_moments")
    op.drop_index("ix_review_questions_video_id", table_name="review_questions")
    op.drop_table("review_questions")
    op.drop_index("ix_key_takeaways_video_id", table_name="key_takeaways")
    op.drop_table("key_takeaways")
    op.drop_index("ix_key_concepts_video_id", table_name="key_concepts")
    op.drop_table("key_concepts")
    op.drop_index("ix_ai_summaries_status", table_name="ai_summaries")
    op.drop_table("ai_summaries")
    op.drop_index("ix_ai_summary_jobs_video_id", table_name="ai_summary_jobs")
    op.drop_index("ix_ai_summary_jobs_user_id", table_name="ai_summary_jobs")
    op.drop_index("ix_ai_summary_jobs_status", table_name="ai_summary_jobs")
    op.drop_table("ai_summary_jobs")