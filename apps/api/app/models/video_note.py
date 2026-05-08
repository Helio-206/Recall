from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class VideoNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_notes"
    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_video_notes_user_video"),
        Index("ix_video_notes_user_id", "user_id"),
        Index("ix_video_notes_video_id", "video_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    anchor_timestamp: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped[User] = relationship(back_populates="video_notes")
    video: Mapped[Video] = relationship(back_populates="notes")