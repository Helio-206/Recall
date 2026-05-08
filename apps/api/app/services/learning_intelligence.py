from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue, Retry
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.statuses import COMPLETED, FAILED, PENDING, PROCESSING
from app.models.video import Video
from app.repositories.ai_summaries import AISummaryRepository
from app.repositories.ai_summary_jobs import AISummaryJobRepository
from app.repositories.transcript_segments import TranscriptSegmentRepository
from app.repositories.videos import VideoRepository
from app.schemas.ai_summary import (
    AISummaryJobCreate,
    AISummaryJobRead,
    AISummaryRead,
    ImportantMomentRead,
    KeyConceptRead,
    KeyTakeawayRead,
    ReviewQuestionRead,
    VideoLearningInsightsRead,
)


class LearningInsightsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.videos = VideoRepository(db)
        self.jobs = AISummaryJobRepository(db)
        self.summaries = AISummaryRepository(db)
        self.segments = TranscriptSegmentRepository(db)

    def request_insights(
        self,
        *,
        video_id: UUID,
        user_id: UUID,
        payload: AISummaryJobCreate,
    ) -> AISummaryJobRead:
        video = self._get_video(video_id=video_id, user_id=user_id)
        transcript_segments = self.segments.list_for_video(video.id)
        if not transcript_segments:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Transcript must be completed before AI insights can be generated.",
            )

        active_job = self.jobs.active_for_video(video_id=video_id, user_id=user_id)
        if active_job:
            if active_job.status == PENDING and active_job.attempts == 0 and self._resolved_provider_name() == "heuristic":
                return AISummaryJobRead.model_validate(self._process_inline_job(active_job))
            return AISummaryJobRead.model_validate(active_job)

        summary = self.summaries.get_for_video(video_id)
        if summary and summary.status == COMPLETED and not payload.force:
            latest_job = self.jobs.latest_for_video(video_id=video_id, user_id=user_id)
            if latest_job:
                return AISummaryJobRead.model_validate(latest_job)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This video already has AI insights.",
            )

        job = self._create_and_enqueue(video=video, user_id=user_id, phase="queued")
        self.db.commit()
        self.db.refresh(job)
        return AISummaryJobRead.model_validate(job)

    def get_insights(self, *, video_id: UUID, user_id: UUID) -> VideoLearningInsightsRead:
        video = self._get_video(video_id=video_id, user_id=user_id)
        latest_job = self.jobs.latest_for_video(video_id=video_id, user_id=user_id)
        summary = self.summaries.get_for_video(video_id)

        status_value = summary.status if summary else latest_job.status if latest_job else PENDING
        return VideoLearningInsightsRead(
            video_id=video.id,
            status=status_value,
            summary=AISummaryRead.model_validate(summary) if summary else None,
            key_concepts=[KeyConceptRead.model_validate(item) for item in video.key_concepts],
            key_takeaways=[KeyTakeawayRead.model_validate(item) for item in video.key_takeaways],
            review_questions=[
                ReviewQuestionRead.model_validate(item) for item in video.review_questions
            ],
            important_moments=[
                ImportantMomentRead.model_validate(item) for item in video.important_moments
            ],
            job=AISummaryJobRead.model_validate(latest_job) if latest_job else None,
            error_message=(
                latest_job.error_message
                if latest_job and latest_job.status == FAILED
                else None
            ),
        )

    def get_job_for_user(self, *, job_id: UUID, user_id: UUID) -> AISummaryJobRead:
        job = self.jobs.get_for_user(job_id=job_id, user_id=user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI summary job not found.",
            )
        return AISummaryJobRead.model_validate(job)

    def _get_video(self, *, video_id: UUID, user_id: UUID) -> Video:
        video = self.videos.get_for_user(video_id=video_id, user_id=user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
        return video

    def _create_and_enqueue(self, *, video: Video, user_id: UUID, phase: str):
        summary = self.summaries.get_or_create(
            video_id=video.id,
            prompt_version=self.settings.ai_prompt_version,
        )
        summary.status = PENDING
        job = self.jobs.create(
            user_id=user_id,
            video_id=video.id,
            payload={
                "phase": phase,
                "video_title": video.title,
                "prompt_version": self.settings.ai_prompt_version,
                "provider": self.settings.ai_provider,
                "model": self.settings.openrouter_model,
            },
        )
        self.db.flush()
        self.db.commit()

        if self._resolved_provider_name() == "heuristic":
            return self._process_inline_job(job)

        try:
            self._queue().enqueue(
                "app.workers.ai_summary_worker.process_ai_summary_job",
                str(job.id),
                job_timeout=self.settings.ai_job_timeout_seconds,
                retry=Retry(max=self.settings.ai_retry_attempts, interval=[90]),
            )
        except Exception:
            self.jobs.set_status(
                job,
                status=FAILED,
                error_message="AI summary worker is unavailable.",
                payload=merge_payload(job.payload, phase="failed"),
                finished_at=datetime.now(UTC),
            )
            summary.status = FAILED
            self.db.commit()
        return job

    def _resolved_provider_name(self) -> str:
        provider_name = self.settings.ai_provider.strip().lower()
        if provider_name == "auto":
            return "openrouter" if self.settings.openrouter_api_key else "heuristic"
        return provider_name

    def _process_inline_job(self, job):
        try:
            from app.workers.ai_summary_worker import process_ai_summary_job

            process_ai_summary_job(str(job.id))
        except Exception:
            pass
        refreshed = self.jobs.get(job.id)
        return refreshed or job

    def _queue(self) -> Queue:
        redis = Redis.from_url(self.settings.redis_url)
        return Queue(self.settings.ai_queue_name, connection=redis)


def enqueue_learning_insights_for_video(db: Session, *, video: Video, user_id: UUID) -> None:
    service = LearningInsightsService(db)
    active_job = service.jobs.active_for_video(video_id=video.id, user_id=user_id)
    if active_job:
        return

    summary = service.summaries.get_for_video(video.id)
    if summary and summary.status in {PENDING, PROCESSING, COMPLETED}:
        return

    transcript_segments = service.segments.list_for_video(video.id)
    if not transcript_segments:
        return

    service._create_and_enqueue(video=video, user_id=user_id, phase="queued")


def merge_payload(payload: dict[str, Any], **updates: Any) -> dict[str, Any]:
    return {**(payload or {}), **updates}


def clean_learning_error(error: Exception) -> str:
    if isinstance(error, ValueError):
        return str(error)
    return "AI analysis failed. Try again."