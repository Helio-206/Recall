import logging
from datetime import UTC, datetime
from uuid import UUID

from rq import get_current_job

from app.core.statuses import COMPLETED, FAILED, PENDING, PROCESSING
from app.db.session import SessionLocal
from app.models.space import LearningSpace
from app.repositories.ingestion_jobs import IngestionJobRepository
from app.repositories.sources import SourceRepository
from app.repositories.videos import VideoRepository
from app.services.ingestion_service import clean_error_message, merge_payload
from app.services.metadata_extractor import MetadataExtractor
from app.services.transcripts import enqueue_transcript_for_video

logger = logging.getLogger(__name__)


def process_ingestion_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        jobs = IngestionJobRepository(db)
        sources = SourceRepository(db)
        videos = VideoRepository(db)

        ingestion_job = jobs.get(UUID(job_id))
        if not ingestion_job:
            logger.error("Ingestion job %s was not found.", job_id)
            return

        source = sources.get(ingestion_job.source_id)
        if not source:
            logger.error("Source %s was not found for job %s.", ingestion_job.source_id, job_id)
            return

        now = datetime.now(UTC)
        jobs.mark_processing(ingestion_job, started_at=now)
        sources.set_status(source, status=PROCESSING)
        ingestion_job.payload = merge_payload(
            ingestion_job.payload,
            phase="reading_source",
        )
        db.commit()

        ingestion_job.payload = merge_payload(
            ingestion_job.payload,
            phase="extracting_metadata",
        )
        db.commit()

        extractor = MetadataExtractor()
        extracted_source = extractor.extract(source.url)

        source.source_type = extracted_source.source_type
        source.title = source.title or extracted_source.title
        source.author = extracted_source.author
        source.thumbnail = extracted_source.thumbnail
        source.duration = extracted_source.duration
        ingestion_job.payload = merge_payload(
            ingestion_job.payload,
            phase="structuring_curriculum",
            source_type=extracted_source.source_type,
            detected_count=len(extracted_source.videos),
            added_count=0,
            duplicate_count=0,
            skipped_count=extracted_source.skipped_count,
        )
        db.commit()

        seen_urls = videos.existing_urls_for_space(
            space_id=source.space_id,
            urls={video.url for video in extracted_source.videos},
        )
        order_index = videos.next_order_index(source.space_id)
        added_count = 0
        duplicate_count = 0
        title_override = (ingestion_job.payload or {}).get("title_override")

        for extracted_video in sorted(extracted_source.videos, key=lambda item: item.source_order):
            if extracted_video.url in seen_urls:
                duplicate_count += 1
                continue
            video_title = (
                title_override
                if title_override
                and extracted_source.source_type == "single_video"
                and extracted_video.source_order == 0
                else extracted_video.title
            )
            video = videos.create(
                space_id=source.space_id,
                source_id=source.id,
                title=video_title,
                thumbnail=extracted_video.thumbnail,
                author=extracted_video.author,
                duration=extracted_video.duration,
                url=extracted_video.url,
                order_index=order_index,
                metadata_status=COMPLETED,
                transcript_status=PENDING,
                processing_status=COMPLETED,
            )
            enqueue_transcript_for_video(db, video=video, user_id=source.user_id)
            seen_urls.add(extracted_video.url)
            order_index += 1
            added_count += 1

        completed_at = datetime.now(UTC)
        space = db.get(LearningSpace, source.space_id)
        if space:
            space.updated_at = completed_at
        source.status = COMPLETED
        source.error_message = None
        ingestion_job.payload = merge_payload(
            ingestion_job.payload,
            phase="completed",
            added_count=added_count,
            duplicate_count=max(duplicate_count, 0),
        )
        jobs.set_status(
            ingestion_job,
            status=COMPLETED,
            finished_at=completed_at,
            error_message=None,
            payload=ingestion_job.payload,
        )
        db.commit()
    except Exception as exc:
        logger.exception("Ingestion job %s failed.", job_id)
        db.rollback()
        _mark_failed_or_retry(job_id=job_id, error=exc)
        raise
    finally:
        db.close()


def _mark_failed_or_retry(*, job_id: str, error: Exception) -> None:
    db = SessionLocal()
    try:
        jobs = IngestionJobRepository(db)
        sources = SourceRepository(db)
        ingestion_job = jobs.get(UUID(job_id))
        if not ingestion_job:
            return
        source = sources.get(ingestion_job.source_id)
        message = clean_error_message(error)
        rq_job = get_current_job()
        retries_left = getattr(rq_job, "retries_left", 0) if rq_job else 0
        next_status = PENDING if retries_left else FAILED
        payload = merge_payload(
            ingestion_job.payload,
            phase="retrying" if retries_left else "failed",
        )
        jobs.set_status(
            ingestion_job,
            status=next_status,
            payload=payload,
            error_message=message,
            finished_at=datetime.now(UTC) if not retries_left else None,
        )
        if source:
            sources.set_status(source, status=next_status, error_message=message)
        db.commit()
    finally:
        db.close()
