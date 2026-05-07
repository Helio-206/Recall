from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue, Retry, Worker
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.statuses import FAILED, PENDING
from app.repositories.ingestion_jobs import IngestionJobRepository
from app.repositories.sources import SourceRepository
from app.repositories.spaces import LearningSpaceRepository
from app.schemas.ingestion import IngestionAccepted, IngestionJobRead, IngestionRequest
from app.schemas.source import SourceRead
from app.services.metadata_extractor import MetadataExtractionError, MetadataExtractor


class IngestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.spaces = LearningSpaceRepository(db)
        self.sources = SourceRepository(db)
        self.jobs = IngestionJobRepository(db)
        self.extractor = MetadataExtractor()

    def ingest(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
        payload: IngestionRequest,
    ) -> IngestionAccepted:
        space = self.spaces.get_for_user(space_id=space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )

        url = self.extractor.validate_youtube_url(str(payload.url))
        try:
            source_type = self.extractor.detect_source_type(url)
        except MetadataExtractionError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(exc),
            ) from exc

        if source_type == "channel":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Channel ingestion is not available yet.",
            )

        queue = self._queue()
        self._ensure_worker_available(queue)

        source = self.sources.create(
            user_id=user_id,
            space_id=space_id,
            url=url,
            platform="youtube",
            source_type=source_type,
            title=payload.title,
        )
        job = self.jobs.create(
            user_id=user_id,
            space_id=space_id,
            source_id=source.id,
            type="metadata_extraction",
            payload={
                "url": url,
                "title_override": payload.title,
                "source_type": source_type,
                "phase": "queued",
                "detected_count": 0,
                "added_count": 0,
                "duplicate_count": 0,
                "skipped_count": 0,
            },
        )
        self.db.commit()

        try:
            queue.enqueue(
                "app.workers.ingestion_worker.process_ingestion_job",
                str(job.id),
                job_timeout=self.settings.ingestion_job_timeout_seconds,
                retry=Retry(max=self.settings.ingestion_retry_attempts, interval=[15, 60]),
            )
        except Exception as exc:
            db_job = self.jobs.get(job.id)
            db_source = self.sources.get(source.id)
            if db_job and db_source:
                self.jobs.set_status(
                    db_job,
                    status="failed",
                    error_message=worker_unavailable_message(),
                    payload={**db_job.payload, "phase": "failed"},
                )
                self.sources.set_status(
                    db_source,
                    status="failed",
                    error_message=worker_unavailable_message(),
                )
                self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=worker_unavailable_message(),
            ) from exc

        return IngestionAccepted(job_id=job.id, source_id=source.id, status=PENDING)

    def get_job_for_user(self, *, job_id: UUID, user_id: UUID) -> IngestionJobRead:
        job = self.jobs.get_for_user(job_id=job_id, user_id=user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ingestion job not found.",
            )
        if job.status == PENDING and not self._has_registered_worker():
            db_source = self.sources.get(job.source_id)
            self.jobs.set_status(
                job,
                status=FAILED,
                error_message=worker_unavailable_message(),
                payload=merge_payload(job.payload, phase="failed"),
                finished_at=datetime.now(UTC),
            )
            if db_source:
                self.sources.set_status(
                    db_source,
                    status=FAILED,
                    error_message=worker_unavailable_message(),
                )
            self.db.commit()
        return IngestionJobRead.model_validate(job)

    def list_sources_for_space(self, *, space_id: UUID, user_id: UUID) -> list[SourceRead]:
        space = self.spaces.get_for_user(space_id=space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )
        return [
            SourceRead.model_validate(source)
            for source in self.sources.list_for_space(space_id=space_id, user_id=user_id)
        ]

    def _queue(self) -> Queue:
        redis = Redis.from_url(self.settings.redis_url)
        return Queue(self.settings.ingestion_queue_name, connection=redis)

    def _has_registered_worker(self) -> bool:
        try:
            queue = self._queue()
            return bool(Worker.all(connection=queue.connection, queue=queue))
        except Exception:
            return False

    def _ensure_worker_available(self, queue: Queue) -> None:
        try:
            workers = Worker.all(connection=queue.connection, queue=queue)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=worker_unavailable_message(),
            ) from exc

        if not workers:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=worker_unavailable_message(),
            )


def clean_error_message(error: Exception) -> str:
    if isinstance(error, MetadataExtractionError):
        return str(error)
    return "We could not extract metadata from that source."


def merge_payload(payload: dict[str, Any], **updates: Any) -> dict[str, Any]:
    return {**(payload or {}), **updates}


def worker_unavailable_message() -> str:
    return "The metadata worker is offline. Start the ingestion worker and try again."
