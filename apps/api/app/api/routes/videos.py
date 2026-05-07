from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.video import VideoRead, VideoUpdate
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


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_video(
    video_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    VideoService(db).delete(video_id=video_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
