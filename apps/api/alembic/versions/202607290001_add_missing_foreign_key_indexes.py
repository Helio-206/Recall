"""add missing foreign key indexes

Revision ID: 202607290001
Revises: 202605080003
Create Date: 2026-07-29 13:20:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202607290001"
down_revision: str | None = "202605080003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_extension_save_events_ingestion_job_id",
        "extension_save_events",
        ["ingestion_job_id"],
        unique=False,
    )
    op.create_index(
        "ix_extension_save_events_source_id",
        "extension_save_events",
        ["source_id"],
        unique=False,
    )
    op.create_index("ix_ingestion_jobs_source_id", "ingestion_jobs", ["source_id"], unique=False)
    op.create_index("ix_ingestion_jobs_space_id", "ingestion_jobs", ["space_id"], unique=False)
    op.create_index(
        "ix_search_result_clicks_space_id",
        "search_result_clicks",
        ["space_id"],
        unique=False,
    )
    op.create_index(
        "ix_search_result_clicks_video_id",
        "search_result_clicks",
        ["video_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_search_result_clicks_video_id", table_name="search_result_clicks")
    op.drop_index("ix_search_result_clicks_space_id", table_name="search_result_clicks")
    op.drop_index("ix_ingestion_jobs_space_id", table_name="ingestion_jobs")
    op.drop_index("ix_ingestion_jobs_source_id", table_name="ingestion_jobs")
    op.drop_index("ix_extension_save_events_source_id", table_name="extension_save_events")
    op.drop_index("ix_extension_save_events_ingestion_job_id", table_name="extension_save_events")
