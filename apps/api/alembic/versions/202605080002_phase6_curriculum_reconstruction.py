"""phase 6 curriculum reconstruction

Revision ID: 202605080002
Revises: 202605080001
Create Date: 2026-05-08 00:20:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "202605080002"
down_revision: str | None = "202605080001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "curriculum_reconstruction_jobs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
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
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_curriculum_reconstruction_jobs_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_curriculum_reconstruction_jobs_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_curriculum_reconstruction_jobs")),
    )
    op.create_index(
        "ix_curriculum_reconstruction_jobs_space_id",
        "curriculum_reconstruction_jobs",
        ["space_id"],
        unique=False,
    )
    op.create_index(
        "ix_curriculum_reconstruction_jobs_status",
        "curriculum_reconstruction_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_curriculum_reconstruction_jobs_user_id",
        "curriculum_reconstruction_jobs",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "learning_modules",
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reconstruction_job_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("difficulty_level", sa.String(length=24), nullable=False),
        sa.Column(
            "learning_objectives",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=True),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
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
            ["reconstruction_job_id"],
            ["curriculum_reconstruction_jobs.id"],
            name=op.f(
                "fk_learning_modules_reconstruction_job_id_curriculum_reconstruction_jobs"
            ),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_learning_modules_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_modules")),
        sa.UniqueConstraint("space_id", "order_index", name="uq_learning_modules_space_order"),
    )
    op.create_index(
        "ix_learning_modules_job_id",
        "learning_modules",
        ["reconstruction_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_learning_modules_space_difficulty",
        "learning_modules",
        ["space_id", "difficulty_level"],
        unique=False,
    )
    op.create_index("ix_learning_modules_space_id", "learning_modules", ["space_id"], unique=False)

    op.create_table(
        "video_curriculum_profiles",
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("primary_topic", sa.String(length=180), nullable=False),
        sa.Column("subtopics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("difficulty_level", sa.String(length=24), nullable=False),
        sa.Column(
            "prerequisite_topics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("extracted_keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("module_hint", sa.String(length=180), nullable=True),
        sa.Column(
            "redundancy_signals",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("estimated_sequence_score", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("prompt_version", sa.String(length=40), nullable=False),
        sa.Column("manual_module_title", sa.String(length=180), nullable=True),
        sa.Column("manual_order_index", sa.Integer(), nullable=True),
        sa.Column("manual_override_locked", sa.Boolean(), nullable=False),
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
            name=op.f("fk_video_curriculum_profiles_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_video_curriculum_profiles_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_video_curriculum_profiles")),
        sa.UniqueConstraint("video_id", name="uq_video_curriculum_profiles_video_id"),
    )
    op.create_index(
        "ix_video_curriculum_profiles_difficulty",
        "video_curriculum_profiles",
        ["difficulty_level"],
        unique=False,
    )
    op.create_index(
        "ix_video_curriculum_profiles_primary_topic",
        "video_curriculum_profiles",
        ["primary_topic"],
        unique=False,
    )
    op.create_index(
        "ix_video_curriculum_profiles_space_id",
        "video_curriculum_profiles",
        ["space_id"],
        unique=False,
    )

    op.create_table(
        "module_videos",
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("is_manual_override", sa.Boolean(), nullable=False),
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
            ["module_id"],
            ["learning_modules.id"],
            name=op.f("fk_module_videos_module_id_learning_modules"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["video_id"],
            ["videos.id"],
            name=op.f("fk_module_videos_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_module_videos")),
        sa.UniqueConstraint("module_id", "order_index", name="uq_module_videos_module_order"),
        sa.UniqueConstraint("module_id", "video_id", name="uq_module_videos_module_video"),
    )
    op.create_index("ix_module_videos_module_id", "module_videos", ["module_id"], unique=False)
    op.create_index("ix_module_videos_video_id", "module_videos", ["video_id"], unique=False)

    op.create_table(
        "video_dependencies",
        sa.Column("space_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prerequisite_video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependent_video_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", sa.String(length=40), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
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
            ["dependent_video_id"],
            ["videos.id"],
            name=op.f("fk_video_dependencies_dependent_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["prerequisite_video_id"],
            ["videos.id"],
            name=op.f("fk_video_dependencies_prerequisite_video_id_videos"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["space_id"],
            ["learning_spaces.id"],
            name=op.f("fk_video_dependencies_space_id_learning_spaces"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_video_dependencies")),
        sa.UniqueConstraint(
            "prerequisite_video_id",
            "dependent_video_id",
            name="uq_video_dependencies_edge",
        ),
    )
    op.create_index(
        "ix_video_dependencies_dependent",
        "video_dependencies",
        ["dependent_video_id"],
        unique=False,
    )
    op.create_index(
        "ix_video_dependencies_prerequisite",
        "video_dependencies",
        ["prerequisite_video_id"],
        unique=False,
    )
    op.create_index(
        "ix_video_dependencies_space_id",
        "video_dependencies",
        ["space_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_video_dependencies_space_id", table_name="video_dependencies")
    op.drop_index("ix_video_dependencies_prerequisite", table_name="video_dependencies")
    op.drop_index("ix_video_dependencies_dependent", table_name="video_dependencies")
    op.drop_table("video_dependencies")
    op.drop_index("ix_module_videos_video_id", table_name="module_videos")
    op.drop_index("ix_module_videos_module_id", table_name="module_videos")
    op.drop_table("module_videos")
    op.drop_index(
        "ix_video_curriculum_profiles_space_id",
        table_name="video_curriculum_profiles",
    )
    op.drop_index(
        "ix_video_curriculum_profiles_primary_topic",
        table_name="video_curriculum_profiles",
    )
    op.drop_index(
        "ix_video_curriculum_profiles_difficulty",
        table_name="video_curriculum_profiles",
    )
    op.drop_table("video_curriculum_profiles")
    op.drop_index("ix_learning_modules_space_id", table_name="learning_modules")
    op.drop_index("ix_learning_modules_space_difficulty", table_name="learning_modules")
    op.drop_index("ix_learning_modules_job_id", table_name="learning_modules")
    op.drop_table("learning_modules")
    op.drop_index(
        "ix_curriculum_reconstruction_jobs_user_id",
        table_name="curriculum_reconstruction_jobs",
    )
    op.drop_index(
        "ix_curriculum_reconstruction_jobs_status",
        table_name="curriculum_reconstruction_jobs",
    )
    op.drop_index(
        "ix_curriculum_reconstruction_jobs_space_id",
        table_name="curriculum_reconstruction_jobs",
    )
    op.drop_table("curriculum_reconstruction_jobs")