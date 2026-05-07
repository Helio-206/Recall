from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ingestion import IngestionAccepted, IngestionRequest
from app.schemas.source import SourceRead
from app.schemas.space import (
    LearningSpaceCreate,
    LearningSpaceDetail,
    LearningSpaceRead,
    LearningSpaceUpdate,
)
from app.schemas.video import VideoCreate, VideoRead
from app.services.ingestion_service import IngestionService
from app.services.spaces import LearningSpaceService
from app.services.videos import VideoService

router = APIRouter()


@router.get("", response_model=list[LearningSpaceRead])
def list_spaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LearningSpaceRead]:
    return LearningSpaceService(db).list_for_user(current_user.id)


@router.post("", response_model=LearningSpaceDetail, status_code=status.HTTP_201_CREATED)
def create_space(
    payload: LearningSpaceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningSpaceDetail:
    return LearningSpaceService(db).create(user_id=current_user.id, payload=payload)


@router.get("/{space_id}", response_model=LearningSpaceDetail)
def get_space(
    space_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningSpaceDetail:
    return LearningSpaceService(db).get_for_user(space_id=space_id, user_id=current_user.id)


@router.patch("/{space_id}", response_model=LearningSpaceDetail)
def update_space(
    space_id: UUID,
    payload: LearningSpaceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LearningSpaceDetail:
    return LearningSpaceService(db).update(
        space_id=space_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_space(
    space_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    LearningSpaceService(db).delete(space_id=space_id, user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{space_id}/videos", response_model=VideoRead, status_code=status.HTTP_201_CREATED)
def add_video(
    space_id: UUID,
    payload: VideoCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VideoRead:
    return VideoService(db).add_to_space(
        space_id=space_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.post(
    "/{space_id}/ingest",
    response_model=IngestionAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
def ingest_source(
    space_id: UUID,
    payload: IngestionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngestionAccepted:
    return IngestionService(db).ingest(space_id=space_id, user_id=current_user.id, payload=payload)


@router.get("/{space_id}/sources", response_model=list[SourceRead])
def list_sources(
    space_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SourceRead]:
    return IngestionService(db).list_sources_for_space(space_id=space_id, user_id=current_user.id)


@router.get("/{space_id}/videos", response_model=list[VideoRead])
def list_videos(
    space_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[VideoRead]:
    return VideoService(db).list_for_space(space_id=space_id, user_id=current_user.id)
