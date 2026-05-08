from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_summary_job import AISummaryJob


class AISummaryJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        video_id: UUID,
        payload: dict[str, Any],
    ) -> AISummaryJob:
        job = AISummaryJob(user_id=user_id, video_id=video_id, payload=payload)
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: UUID) -> AISummaryJob | None:
        return self.db.get(AISummaryJob, job_id)

    def get_for_user(self, *, job_id: UUID, user_id: UUID) -> AISummaryJob | None:
        stmt = select(AISummaryJob).where(AISummaryJob.id == job_id, AISummaryJob.user_id == user_id)
        return self.db.scalar(stmt)

    def latest_for_video(self, *, video_id: UUID, user_id: UUID) -> AISummaryJob | None:
        stmt = (
            select(AISummaryJob)
            .where(AISummaryJob.video_id == video_id, AISummaryJob.user_id == user_id)
            .order_by(AISummaryJob.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def active_for_video(self, *, video_id: UUID, user_id: UUID) -> AISummaryJob | None:
        stmt = (
            select(AISummaryJob)
            .where(
                AISummaryJob.video_id == video_id,
                AISummaryJob.user_id == user_id,
                AISummaryJob.status.in_(("pending", "processing")),
            )
            .order_by(AISummaryJob.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def mark_processing(self, job: AISummaryJob, *, started_at: datetime) -> AISummaryJob:
        job.status = "processing"
        job.started_at = job.started_at or started_at
        job.finished_at = None
        job.error_message = None
        job.attempts += 1
        self.db.flush()
        return job

    def set_status(
        self,
        job: AISummaryJob,
        *,
        status: str,
        payload: dict[str, Any] | None = None,
        error_message: str | None = None,
        finished_at: datetime | None = None,
    ) -> AISummaryJob:
        job.status = status
        job.error_message = error_message
        if payload is not None:
            job.payload = payload
        if finished_at is not None:
            job.finished_at = finished_at
        self.db.flush()
        return job