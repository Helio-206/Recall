from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.space import LearningSpace
from app.models.video import Video


class VideoRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_user(self, *, video_id: UUID, user_id: UUID) -> Video | None:
        stmt = (
            select(Video)
            .join(LearningSpace, LearningSpace.id == Video.space_id)
            .where(Video.id == video_id, LearningSpace.user_id == user_id)
        )
        return self.db.scalar(stmt)

    def list_for_space(self, *, space_id: UUID, user_id: UUID) -> list[Video]:
        stmt = (
            select(Video)
            .join(LearningSpace, LearningSpace.id == Video.space_id)
            .where(Video.space_id == space_id, LearningSpace.user_id == user_id)
            .order_by(Video.order_index.asc(), Video.created_at.asc())
        )
        return list(self.db.scalars(stmt).all())

    def existing_urls_for_space(self, *, space_id: UUID, urls: set[str]) -> set[str]:
        if not urls:
            return set()
        stmt = select(Video.url).where(Video.space_id == space_id, Video.url.in_(urls))
        return set(self.db.scalars(stmt).all())

    def next_order_index(self, space_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(Video.order_index), -1) + 1).where(
            Video.space_id == space_id
        )
        return int(self.db.scalar(stmt) or 0)

    def create(
        self,
        *,
        space_id: UUID,
        title: str,
        thumbnail: str | None,
        author: str | None,
        duration: int | None,
        url: str,
        order_index: int,
        source_id: UUID | None = None,
        metadata_status: str = "completed",
        transcript_status: str = "pending",
        processing_status: str = "completed",
    ) -> Video:
        video = Video(
            space_id=space_id,
            source_id=source_id,
            title=title,
            thumbnail=thumbnail,
            author=author,
            duration=duration,
            url=url,
            order_index=order_index,
            metadata_status=metadata_status,
            transcript_status=transcript_status,
            processing_status=processing_status,
        )
        self.db.add(video)
        self.db.flush()
        return video

    def delete(self, video: Video) -> None:
        self.db.delete(video)
        self.db.flush()
