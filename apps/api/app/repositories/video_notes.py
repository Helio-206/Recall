from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.video_note import VideoNote


class VideoNoteRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_video(self, *, video_id: UUID, user_id: UUID) -> VideoNote | None:
        stmt = select(VideoNote).where(VideoNote.video_id == video_id, VideoNote.user_id == user_id)
        return self.db.scalar(stmt)

    def create(
        self,
        *,
        video_id: UUID,
        user_id: UUID,
        title: str | None,
        content: str,
        anchor_timestamp: float | None,
    ) -> VideoNote:
        note = VideoNote(
            video_id=video_id,
            user_id=user_id,
            title=title,
            content=content,
            anchor_timestamp=anchor_timestamp,
        )
        self.db.add(note)
        self.db.flush()
        return note

    def delete(self, note: VideoNote) -> None:
        self.db.delete(note)
        self.db.flush()