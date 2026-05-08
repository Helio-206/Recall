import logging
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID

from rq import get_current_job

from app.core.config import get_settings
from app.core.statuses import COMPLETED, FAILED, PENDING, PROCESSING
from app.db.session import SessionLocal
from app.repositories.transcript_jobs import TranscriptJobRepository
from app.repositories.transcript_segments import TranscriptSegmentRepository
from app.repositories.videos import VideoRepository
from app.services.audio_extractor import TemporaryAudioExtractor
from app.services.caption_extractor import CaptionExtractionError, YouTubeCaptionExtractor
from app.services.search_indexing import sync_video_search_documents
from app.services.transcription_engine import WhisperTranscriber
from app.services.transcripts import clean_transcript_error, merge_payload

logger = logging.getLogger(__name__)


def process_transcript_job(job_id: str) -> None:
    db = SessionLocal()
    try:
        jobs = TranscriptJobRepository(db)
        segments = TranscriptSegmentRepository(db)
        videos = VideoRepository(db)

        transcript_job = jobs.get(UUID(job_id))
        if not transcript_job:
            logger.error("Transcript job %s was not found.", job_id)
            return
        if transcript_job.status == COMPLETED:
            logger.info("Transcript job %s was already completed. Skipping worker execution.", job_id)
            return

        video = videos.get(transcript_job.video_id)
        if not video:
            logger.error(
                "Video %s was not found for transcript job %s.",
                transcript_job.video_id,
                job_id,
            )
            return

        started_at = datetime.now(UTC)
        jobs.mark_processing(transcript_job, started_at=started_at)
        video.transcript_status = PROCESSING
        video.processing_status = PROCESSING
        transcript_job.payload = merge_payload(transcript_job.payload, phase="preparing_audio")
        db.commit()

        settings = get_settings()
        settings.transcript_tmp_path.mkdir(parents=True, exist_ok=True)

        captions = None
        if settings.transcript_prefer_youtube_captions:
            transcript_job.payload = merge_payload(
                transcript_job.payload,
                phase="fetching_captions",
            )
            db.commit()
            try:
                captions = YouTubeCaptionExtractor().extract(video_url=video.url)
            except CaptionExtractionError as exc:
                logger.info("Caption extraction skipped for transcript job %s: %s", job_id, exc)
                transcript_job.payload = merge_payload(
                    transcript_job.payload,
                    caption_error=str(exc),
                )
                db.commit()

        if captions:
            transcript_job.payload = merge_payload(
                transcript_job.payload,
                phase="structuring_transcript",
                segments_count=len(captions.segments),
                method=captions.source,
                language=captions.language,
            )
            db.commit()
            segments.replace_for_video(video_id=video.id, segments=captions.segments)
        else:
            with TemporaryDirectory(
                prefix=f"recall-transcript-{job_id}-",
                dir=settings.transcript_tmp_path,
            ) as temp_dir:
                audio_path = TemporaryAudioExtractor().extract(
                    video_url=video.url,
                    output_dir=Path(temp_dir),
                )

                transcript_job.payload = merge_payload(
                    transcript_job.payload,
                    phase="generating_transcript",
                    method="whisper",
                )
                db.commit()

                drafts = WhisperTranscriber().transcribe(audio_path)
                transcript_job.payload = merge_payload(
                    transcript_job.payload,
                    phase="structuring_transcript",
                    segments_count=len(drafts),
                )
                db.commit()

                segments.replace_for_video(video_id=video.id, segments=drafts)

        completed_at = datetime.now(UTC)
        transcript_job.payload = merge_payload(
            transcript_job.payload,
            phase="finalizing_document",
        )
        db.commit()

        video.transcript_status = COMPLETED
        video.processing_status = COMPLETED
        jobs.set_status(
            transcript_job,
            status=COMPLETED,
            payload=merge_payload(transcript_job.payload, phase="completed"),
            error_message=None,
            finished_at=completed_at,
        )
        db.commit()
        sync_video_search_documents(db, video_id=video.id)
        db.commit()
    except Exception as exc:
        logger.exception("Transcript job %s failed.", job_id)
        db.rollback()
        _mark_failed_or_retry(job_id=job_id, error=exc)
        raise
    finally:
        db.close()


def _mark_failed_or_retry(*, job_id: str, error: Exception) -> None:
    db = SessionLocal()
    try:
        jobs = TranscriptJobRepository(db)
        videos = VideoRepository(db)
        transcript_job = jobs.get(UUID(job_id))
        if not transcript_job:
            return

        video = videos.get(transcript_job.video_id)
        message = clean_transcript_error(error)
        rq_job = get_current_job()
        retries_left = getattr(rq_job, "retries_left", 0) if rq_job else 0
        next_status = PENDING if retries_left else FAILED
        payload = merge_payload(
            transcript_job.payload,
            phase="retrying" if retries_left else "failed",
        )
        jobs.set_status(
            transcript_job,
            status=next_status,
            payload=payload,
            error_message=message,
            finished_at=datetime.now(UTC) if not retries_left else None,
        )
        if video:
            video.transcript_status = next_status
            video.processing_status = COMPLETED if next_status == FAILED else PROCESSING
        db.commit()
    finally:
        db.close()
