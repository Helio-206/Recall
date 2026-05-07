from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.spaces import LearningSpaceRepository
from app.repositories.videos import VideoRepository
from app.schemas.video import VideoCreate, VideoRead, VideoUpdate
from app.services.metadata import MetadataService


class VideoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.spaces = LearningSpaceRepository(db)
        self.videos = VideoRepository(db)
        self.metadata = MetadataService()

    def add_to_space(self, *, space_id: UUID, user_id: UUID, payload: VideoCreate) -> VideoRead:
        space = self.spaces.get_for_user(space_id=space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
        )

        metadata = self.metadata.extract(url=str(payload.url), title_override=payload.title)
        existing_urls = self.videos.existing_urls_for_space(
            space_id=space.id,
            urls={metadata.url},
        )
        if metadata.url in existing_urls:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This video is already in the Learning Space.",
            )

        video = self.videos.create(
            space_id=space.id,
            title=metadata.title,
            thumbnail=metadata.thumbnail,
            author=metadata.author,
            duration=metadata.duration,
            url=metadata.url,
            order_index=self.videos.next_order_index(space.id),
        )
        space.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(video)
        return VideoRead.model_validate(video)

    def list_for_space(self, *, space_id: UUID, user_id: UUID) -> list[VideoRead]:
        space = self.spaces.get_for_user(space_id=space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )
        return [
            VideoRead.model_validate(video)
            for video in self.videos.list_for_space(space_id=space_id, user_id=user_id)
        ]

    def update(self, *, video_id: UUID, user_id: UUID, payload: VideoUpdate) -> VideoRead:
        video = self.videos.get_for_user(video_id=video_id, user_id=user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(video, key, value.strip() if isinstance(value, str) else value)
        video.space.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(video)
        return VideoRead.model_validate(video)

    def delete(self, *, video_id: UUID, user_id: UUID) -> None:
        video = self.videos.get_for_user(video_id=video_id, user_id=user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
        video.space.updated_at = datetime.now(UTC)
        self.videos.delete(video)
        self.db.commit()
