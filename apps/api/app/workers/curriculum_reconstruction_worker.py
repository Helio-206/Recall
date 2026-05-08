import logging
from datetime import UTC, datetime
from uuid import UUID

from rq import get_current_job

from app.core.statuses import FAILED, PENDING
from app.db.session import SessionLocal
from app.repositories.curriculum_reconstruction_jobs import CurriculumReconstructionJobRepository
from app.services.curriculum_reconstruction import (
    CurriculumReconstructionService,
    clean_curriculum_error,
    merge_payload,
)

logger = logging.getLogger(__name__)


def process_curriculum_reconstruction_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        CurriculumReconstructionService(db).process_job(job_id=UUID(job_id))
    except Exception as exc:
        logger.exception("Curriculum reconstruction job %s failed.", job_id)
        db.rollback()
        _mark_failed_or_retry(job_id=job_id, error=exc)
        raise
    finally:
        db.close()


def _mark_failed_or_retry(*, job_id: str, error: Exception) -> None:
    db = SessionLocal()
    try:
        jobs = CurriculumReconstructionJobRepository(db)
        reconstruction_job = jobs.get(UUID(job_id))
        if not reconstruction_job:
            return

        message = clean_curriculum_error(error)
        rq_job = get_current_job()
        retries_left = getattr(rq_job, "retries_left", 0) if rq_job else 0
        next_status = PENDING if retries_left else FAILED
        jobs.set_status(
            reconstruction_job,
            status=next_status,
            payload=merge_payload(
                reconstruction_job.payload,
                phase="retrying" if retries_left else "failed",
            ),
            error_message=message,
            finished_at=datetime.now(UTC) if not retries_left else None,
        )
        db.commit()
    finally:
        db.close()