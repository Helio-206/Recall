from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue, Retry
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.statuses import COMPLETED, FAILED, PENDING, PROCESSING
from app.models.transcript_job import TranscriptJob
from app.models.video import Video
from app.repositories.transcript_jobs import TranscriptJobRepository
from app.repositories.transcript_segments import TranscriptSegmentRepository
from app.repositories.videos import VideoRepository
from app.schemas.transcript import (
    TranscriptJobCreate,
    TranscriptJobRead,
    TranscriptSegmentRead,
    VideoTranscriptRead,
)
from app.services.caption_extractor import CaptionExtractionError, YouTubeCaptionExtractor
from app.services.search_indexing import sync_video_search_documents


class TranscriptService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.videos = VideoRepository(db)
        self.jobs = TranscriptJobRepository(db)
        self.segments = TranscriptSegmentRepository(db)

    def request_transcript(
        self,
        *,
        video_id: UUID,
        user_id: UUID,
        payload: TranscriptJobCreate,
    ) -> TranscriptJobRead:
        video = self._get_video(video_id=video_id, user_id=user_id)

        active_job = self.jobs.active_for_video(video_id=video_id, user_id=user_id)
        if active_job:
            if active_job.status == PENDING and active_job.attempts == 0:
                fast_job = self._try_complete_with_captions(
                    video=video,
                    user_id=user_id,
                    existing_job=active_job,
                )
                if fast_job:
                    self.db.refresh(fast_job)
                    return TranscriptJobRead.model_validate(fast_job)
            return TranscriptJobRead.model_validate(active_job)

        existing_segments = self.segments.list_for_video(video_id)
        if existing_segments and video.transcript_status == COMPLETED and not payload.force:
            latest_job = self.jobs.latest_for_video(video_id=video_id, user_id=user_id)
            if latest_job:
                return TranscriptJobRead.model_validate(latest_job)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This video already has a transcript.",
            )

        fast_job = self._try_complete_with_captions(video=video, user_id=user_id)
        if fast_job:
            self.db.refresh(fast_job)
            return TranscriptJobRead.model_validate(fast_job)

        job = self._create_and_enqueue(video=video, user_id=user_id, phase="queued")
        self.db.commit()
        self.db.refresh(job)
        return TranscriptJobRead.model_validate(job)

    def get_transcript(self, *, video_id: UUID, user_id: UUID) -> VideoTranscriptRead:
        video = self._get_video(video_id=video_id, user_id=user_id)
        latest_job = self.jobs.latest_for_video(video_id=video_id, user_id=user_id)
        segments = self.segments.list_for_video(video_id)
        return VideoTranscriptRead(
            video_id=video.id,
            status=video.transcript_status,
            segments=[TranscriptSegmentRead.model_validate(segment) for segment in segments],
            job=TranscriptJobRead.model_validate(latest_job) if latest_job else None,
            error_message=(
                latest_job.error_message if latest_job and latest_job.status == FAILED else None
            ),
        )

    def get_job_for_user(self, *, job_id: UUID, user_id: UUID) -> TranscriptJobRead:
        job = self.jobs.get_for_user(job_id=job_id, user_id=user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript job not found.",
            )
        return TranscriptJobRead.model_validate(job)

    def _get_video(self, *, video_id: UUID, user_id: UUID) -> Video:
        video = self.videos.get_for_user(video_id=video_id, user_id=user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
        return video

    def _create_and_enqueue(self, *, video: Video, user_id: UUID, phase: str) -> TranscriptJob:
        video.transcript_status = PENDING
        job = self.jobs.create(
            user_id=user_id,
            video_id=video.id,
            payload={
                "phase": phase,
                "video_url": video.url,
                "segments_count": 0,
                "model": self.settings.whisper_model_name,
            },
        )
        self.db.flush()
        self.db.commit()
        try:
            self._queue().enqueue(
                "app.workers.transcript_worker.process_transcript_job",
                str(job.id),
                job_timeout=self.settings.transcript_job_timeout_seconds,
                retry=Retry(max=self.settings.transcript_retry_attempts, interval=[60]),
            )
        except Exception:
            self.jobs.set_status(
                job,
                status=FAILED,
                error_message="Transcript worker is unavailable.",
                payload=merge_payload(job.payload, phase="failed"),
                finished_at=datetime.now(UTC),
            )
            video.transcript_status = FAILED
            self.db.commit()
        return job

    def _try_complete_with_captions(
        self,
        *,
        video: Video,
        user_id: UUID,
        existing_job: TranscriptJob | None = None,
    ) -> TranscriptJob | None:
        if not self.settings.transcript_prefer_youtube_captions:
            return None

        try:
            captions = YouTubeCaptionExtractor().extract(video_url=video.url)
        except CaptionExtractionError:
            return None

        if not captions:
            return None

        started_at = datetime.now(UTC)
        video.transcript_status = PROCESSING
        video.processing_status = PROCESSING
        if existing_job:
            job = existing_job
            job.payload = merge_payload(
                job.payload,
                phase="fetching_captions",
                video_url=video.url,
                segments_count=len(captions.segments),
                method=captions.source,
                language=captions.language,
                model="youtube-captions",
            )
        else:
            job = self.jobs.create(
                user_id=user_id,
                video_id=video.id,
                payload={
                    "phase": "fetching_captions",
                    "video_url": video.url,
                    "segments_count": len(captions.segments),
                    "method": captions.source,
                    "language": captions.language,
                    "model": "youtube-captions",
                },
            )
        self.jobs.mark_processing(job, started_at=started_at)
        job.payload = merge_payload(job.payload, phase="structuring_transcript")
        self.segments.replace_for_video(video_id=video.id, segments=captions.segments)
        video.transcript_status = COMPLETED
        video.processing_status = COMPLETED
        self.jobs.set_status(
            job,
            status=COMPLETED,
            payload=merge_payload(job.payload, phase="completed"),
            error_message=None,
            finished_at=datetime.now(UTC),
        )
        self.db.commit()
        sync_video_search_documents(self.db, video_id=video.id)
        self.db.commit()
        return job

    def _queue(self) -> Queue:
        redis = Redis.from_url(self.settings.redis_url)
        return Queue(self.settings.transcript_queue_name, connection=redis)


def enqueue_transcript_for_video(
    db: Session,
    *,
    video: Video,
    user_id: UUID,
) -> None:
    service = TranscriptService(db)
    active_job = service.jobs.active_for_video(video_id=video.id, user_id=user_id)
    if active_job or video.transcript_status in {PROCESSING, COMPLETED}:
        return
    service._create_and_enqueue(video=video, user_id=user_id, phase="queued")


def clean_transcript_error(error: Exception) -> str:
    from app.services.audio_extractor import AudioExtractionError
    from app.services.caption_extractor import CaptionExtractionError
    from app.services.transcription_engine import TranscriptionError

    if isinstance(error, (AudioExtractionError, CaptionExtractionError, TranscriptionError)):
        return str(error)
    return "Transcript generation failed. Try again."


def merge_payload(payload: dict[str, Any], **updates: Any) -> dict[str, Any]:
    return {**(payload or {}), **updates}
