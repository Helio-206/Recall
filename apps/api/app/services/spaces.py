from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.space import LearningSpace
from app.repositories.spaces import LearningSpaceRepository
from app.schemas.space import (
    LearningSpaceCreate,
    LearningSpaceDetail,
    LearningSpaceRead,
    LearningSpaceUpdate,
)
from app.schemas.video import VideoRead


class LearningSpaceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.spaces = LearningSpaceRepository(db)

    def list_for_user(self, user_id: UUID) -> list[LearningSpaceRead]:
        return [self._serialize(space) for space in self.spaces.list_for_user(user_id)]

    def get_for_user(self, *, space_id: UUID, user_id: UUID) -> LearningSpaceDetail:
        space = self._get_model_for_user(space_id=space_id, user_id=user_id)
        return self._serialize_detail(space)

    def create(self, *, user_id: UUID, payload: LearningSpaceCreate) -> LearningSpaceDetail:
        space = self.spaces.create(
            user_id=user_id,
            title=payload.title,
            description=payload.description,
            topic=payload.topic,
        )
        self.db.commit()
        self.db.refresh(space)
        return self._serialize_detail(space)

    def update(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
        payload: LearningSpaceUpdate,
    ) -> LearningSpaceDetail:
        space = self._get_model_for_user(space_id=space_id, user_id=user_id)
        update_data = payload.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if key == "title" and value is None:
                continue
            setattr(space, key, value.strip() if isinstance(value, str) else value)
        self.db.commit()
        self.db.refresh(space)
        return self._serialize_detail(space)

    def delete(self, *, space_id: UUID, user_id: UUID) -> None:
        space = self._get_model_for_user(space_id=space_id, user_id=user_id)
        self.spaces.delete(space)
        self.db.commit()

    def _get_model_for_user(self, *, space_id: UUID, user_id: UUID) -> LearningSpace:
        space = self.spaces.get_for_user(space_id=space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )
        return space

    @staticmethod
    def _stats(space: LearningSpace) -> dict[str, int]:
        video_count = len(space.videos)
        completed_count = sum(1 for video in space.videos if video.completed)
        progress = round((completed_count / video_count) * 100) if video_count else 0
        return {
            "video_count": video_count,
            "completed_count": completed_count,
            "progress": progress,
        }

    @classmethod
    def _serialize(cls, space: LearningSpace) -> LearningSpaceRead:
        return LearningSpaceRead.model_validate(space).model_copy(update=cls._stats(space))

    @classmethod
    def _serialize_detail(cls, space: LearningSpace) -> LearningSpaceDetail:
        ordered_videos = sorted(space.videos, key=lambda video: video.order_index)
        return LearningSpaceDetail.model_validate(space).model_copy(
            update={
                **cls._stats(space),
                "videos": [VideoRead.model_validate(video) for video in ordered_videos],
            }
        )
