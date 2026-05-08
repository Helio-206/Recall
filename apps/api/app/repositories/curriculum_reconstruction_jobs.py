from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.curriculum_reconstruction_job import CurriculumReconstructionJob


class CurriculumReconstructionJobRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        space_id: UUID,
        provider: str,
        model: str,
        prompt_version: str,
        payload: dict[str, Any],
    ) -> CurriculumReconstructionJob:
        job = CurriculumReconstructionJob(
            user_id=user_id,
            space_id=space_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
            payload=payload,
        )
        self.db.add(job)
        self.db.flush()
        return job

    def get(self, job_id: UUID) -> CurriculumReconstructionJob | None:
        return self.db.get(CurriculumReconstructionJob, job_id)

    def get_for_user(
        self,
        *,
        job_id: UUID,
        user_id: UUID,
    ) -> CurriculumReconstructionJob | None:
        stmt = select(CurriculumReconstructionJob).where(
            CurriculumReconstructionJob.id == job_id,
            CurriculumReconstructionJob.user_id == user_id,
        )
        return self.db.scalar(stmt)

    def latest_for_space(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
    ) -> CurriculumReconstructionJob | None:
        stmt = (
            select(CurriculumReconstructionJob)
            .where(
                CurriculumReconstructionJob.space_id == space_id,
                CurriculumReconstructionJob.user_id == user_id,
            )
            .order_by(CurriculumReconstructionJob.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def active_for_space(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
    ) -> CurriculumReconstructionJob | None:
        stmt = (
            select(CurriculumReconstructionJob)
            .where(
                CurriculumReconstructionJob.space_id == space_id,
                CurriculumReconstructionJob.user_id == user_id,
                CurriculumReconstructionJob.status.in_(("pending", "processing")),
            )
            .order_by(CurriculumReconstructionJob.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def mark_processing(
        self,
        job: CurriculumReconstructionJob,
        *,
        started_at: datetime,
    ) -> CurriculumReconstructionJob:
        job.status = "processing"
        job.started_at = job.started_at or started_at
        job.finished_at = None
        job.error_message = None
        job.attempts += 1
        self.db.flush()
        return job

    def set_status(
        self,
        job: CurriculumReconstructionJob,
        *,
        status: str,
        payload: dict[str, Any] | None = None,
        error_message: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        finished_at: datetime | None = None,
    ) -> CurriculumReconstructionJob:
        job.status = status
        job.error_message = error_message
        if payload is not None:
            job.payload = payload
        if provider is not None:
            job.provider = provider
        if model is not None:
            job.model = model
        if finished_at is not None:
            job.finished_at = finished_at
        self.db.flush()
        return job