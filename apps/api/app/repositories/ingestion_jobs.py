from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ingestion_job import IngestionJob


class IngestionJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        space_id: UUID,
        source_id: UUID,
        type: str,
        payload: dict[str, Any],
    ) -> IngestionJob:
        job = IngestionJob(
            user_id=user_id,
            space_id=space_id,
            source_id=source_id,
            type=type,
            payload=payload,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: UUID) -> IngestionJob | None:
        return self.db.get(IngestionJob, job_id)

    def get_for_user(self, *, job_id: UUID, user_id: UUID) -> IngestionJob | None:
        stmt = select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def mark_processing(self, job: IngestionJob, *, started_at: datetime) -> IngestionJob:
        job.status = "processing"
        job.started_at = job.started_at or started_at
        job.finished_at = None
        job.error_message = None
        job.attempts += 1
        self.db.flush()
        return job

    def set_status(
        self,
        job: IngestionJob,
        *,
        status: str,
        payload: dict[str, Any] | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> IngestionJob:
        job.status = status
        job.error_message = error_message
        if payload is not None:
            job.payload = payload
        if finished_at is not None:
            job.finished_at = finished_at
        self.db.flush()
        return job
