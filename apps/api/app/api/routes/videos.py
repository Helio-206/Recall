from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_summary import AISummaryJobCreate, AISummaryJobRead, VideoLearningInsightsRead
from app.schemas.video_note import VideoNoteRead, VideoNoteUpsert
from app.schemas.transcript import TranscriptJobCreate, TranscriptJobRead, VideoTranscriptRead
from app.schemas.video import VideoRead, VideoUpdate
from app.services.learning_intelligence import LearningInsightsService
from app.services.transcripts import TranscriptService
from app.services.video_notes import VideoNoteService
from app.services.videos import VideoService

router = APIRouter()


@router.patch("/{video_id}", response_model=VideoRead)
def update_video(
    video_id: UUID,
    payload: VideoUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoRead:
    return VideoService(db).update(video_id=video_id, user_id=current_user.id, payload=payload)


@router.get("/{video_id}/transcript", response_model=VideoTranscriptRead)
def get_video_transcript(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoTranscriptRead:
    return TranscriptService(db).get_transcript(video_id=video_id, user_id=current_user.id)


@router.get("/{video_id}/ai-summary", response_model=VideoLearningInsightsRead)
def get_video_ai_summary(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoLearningInsightsRead:
    return LearningInsightsService(db).get_insights(video_id=video_id, user_id=current_user.id)


@router.get("/{video_id}/notes", response_model=VideoNoteRead | None)
def get_video_note(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoNoteRead | None:
    return VideoNoteService(db).get_for_video(video_id=video_id, user_id=current_user.id)


@router.post(
    "/{video_id}/transcript/jobs",
    response_model=TranscriptJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_video_transcript_job(
    video_id: UUID,
    payload: TranscriptJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TranscriptJobRead:
    return TranscriptService(db).request_transcript(
        video_id=video_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.post(
    "/{video_id}/ai-summary/jobs",
    response_model=AISummaryJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def create_video_ai_summary_job(
    video_id: UUID,
    payload: AISummaryJobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISummaryJobRead:
    return LearningInsightsService(db).request_insights(
        video_id=video_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.put("/{video_id}/notes", response_model=VideoNoteRead | None)
def upsert_video_note(
    video_id: UUID,
    payload: VideoNoteUpsert,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoNoteRead | None:
    return VideoNoteService(db).upsert_for_video(
        video_id=video_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    VideoService(db).delete(video_id=video_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
