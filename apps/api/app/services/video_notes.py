from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.video_notes import VideoNoteRepository
from app.repositories.videos import VideoRepository
from app.schemas.video_note import VideoNoteRead, VideoNoteUpsert
from app.services.search_indexing import sync_video_search_documents


class VideoNoteService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.notes = VideoNoteRepository(db)
        self.videos = VideoRepository(db)

    def get_for_video(self, *, video_id: UUID, user_id: UUID) -> VideoNoteRead | None:
        self._get_video(video_id=video_id, user_id=user_id)
        note = self.notes.get_for_video(video_id=video_id, user_id=user_id)
        return VideoNoteRead.model_validate(note) if note else None

    def upsert_for_video(self, *, video_id: UUID, user_id: UUID, payload: VideoNoteUpsert) -> VideoNoteRead | None:
        video = self._get_video(video_id=video_id, user_id=user_id)
        note = self.notes.get_for_video(video_id=video_id, user_id=user_id)

        normalized_title = payload.title.strip() if payload.title else None
        normalized_content = payload.content.strip()
        if not normalized_title and not normalized_content:
            if note:
                self.notes.delete(note)
                self.db.commit()
                sync_video_search_documents(self.db, video_id=video.id)
            return None

        if note:
            note.title = normalized_title
            note.content = normalized_content
            note.anchor_timestamp = payload.anchor_timestamp
        else:
            note = self.notes.create(
                video_id=video.id,
                user_id=user_id,
                title=normalized_title,
                content=normalized_content,
                anchor_timestamp=payload.anchor_timestamp,
            )

        self.db.commit()
        self.db.refresh(note)
        sync_video_search_documents(self.db, video_id=video.id)
        return VideoNoteRead.model_validate(note)

    def _get_video(self, *, video_id: UUID, user_id: UUID):
        video = self.videos.get_for_user(video_id=video_id, user_id=user_id)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")
        return video