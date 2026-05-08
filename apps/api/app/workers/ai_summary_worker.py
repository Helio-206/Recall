import logging
from datetime import UTC, datetime
from uuid import UUID

from rq import get_current_job

from app.core.config import get_settings
from app.core.statuses import COMPLETED, FAILED, PENDING, PROCESSING
from app.db.session import SessionLocal
from app.repositories.ai_summaries import AISummaryRepository
from app.repositories.ai_summary_jobs import AISummaryJobRepository
from app.repositories.transcript_segments import TranscriptSegmentRepository
from app.repositories.videos import VideoRepository
from app.services.ai_chunking import chunk_transcript_segments
from app.services.ai_provider import get_ai_learning_provider
from app.services.learning_intelligence import clean_learning_error, merge_payload
from app.services.search_indexing import sync_video_search_documents

logger = logging.getLogger(__name__)


def process_ai_summary_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        settings = get_settings()
        jobs = AISummaryJobRepository(db)
        summaries = AISummaryRepository(db)
        videos = VideoRepository(db)
        transcript_segments = TranscriptSegmentRepository(db)

        ai_job = jobs.get(UUID(job_id))
        if not ai_job:
            logger.error("AI summary job %s was not found.", job_id)
            return

        video = videos.get(ai_job.video_id)
        if not video:
            logger.error("Video %s was not found for AI job %s.", ai_job.video_id, job_id)
            return

        segments = transcript_segments.list_for_video(video.id)
        if not segments:
            raise ValueError("Transcript must be completed before AI insights can be generated.")

        summary = summaries.get_or_create(video_id=video.id, prompt_version=settings.ai_prompt_version)
        started_at = datetime.now(UTC)
        jobs.mark_processing(ai_job, started_at=started_at)
        summary.status = PROCESSING
        ai_job.payload = merge_payload(ai_job.payload, phase="chunking_transcript")
        db.commit()

        chunks = chunk_transcript_segments(
            segments,
            target_chars=settings.ai_chunk_target_chars,
            overlap_segments=settings.ai_chunk_overlap_segments,
        )

        ai_job.payload = merge_payload(
            ai_job.payload,
            phase="summarizing_chunks",
            chunk_count=len(chunks),
        )
        db.commit()

        provider = get_ai_learning_provider(prompt_version=settings.ai_prompt_version)
        draft = provider.generate(video=video, chunks=chunks, segments=segments)

        ai_job.payload = merge_payload(ai_job.payload, phase="extracting_concepts")
        db.commit()

        ai_job.payload = merge_payload(ai_job.payload, phase="structuring_summary")
        db.commit()

        summaries.replace_children(
            video_id=video.id,
            key_concepts=[(item.concept, item.relevance_score) for item in draft.key_concepts],
            key_takeaways=draft.key_takeaways,
            review_questions=[(item.question, item.answer) for item in draft.review_questions],
            important_moments=[
                (item.title, item.timestamp, item.description) for item in draft.important_moments
            ],
        )
        summary.short_summary = draft.short_summary
        summary.detailed_summary = draft.detailed_summary
        summary.learning_notes = draft.learning_notes
        summary.prompt_version = settings.ai_prompt_version
        summary.status = COMPLETED

        jobs.set_status(
            ai_job,
            status=COMPLETED,
            payload=merge_payload(ai_job.payload, phase="completed"),
            error_message=None,
            finished_at=datetime.now(UTC),
        )
        db.commit()
        sync_video_search_documents(db, video_id=video.id)
    except Exception as exc:
        logger.exception("AI summary job %s failed.", job_id)
        db.rollback()
        _mark_failed_or_retry(job_id=job_id, error=exc)
        raise
    finally:
        db.close()


def _mark_failed_or_retry(*, job_id: str, error: Exception) -> None:
    db = SessionLocal()
    try:
        jobs = AISummaryJobRepository(db)
        summaries = AISummaryRepository(db)
        ai_job = jobs.get(UUID(job_id))
        if not ai_job:
            return

        summary = summaries.get_for_video(ai_job.video_id)
        message = clean_learning_error(error)
        rq_job = get_current_job()
        retries_left = getattr(rq_job, "retries_left", 0) if rq_job else 0
        next_status = PENDING if retries_left else FAILED
        payload = merge_payload(ai_job.payload, phase="retrying" if retries_left else "failed")
        jobs.set_status(
            ai_job,
            status=next_status,
            payload=payload,
            error_message=message,
            finished_at=datetime.now(UTC) if not retries_left else None,
        )
        if summary:
            summary.status = next_status
        db.commit()
    finally:
        db.close()