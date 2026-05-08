from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.space import LearningSpace
    from app.models.transcript_job import TranscriptJob
    from app.models.transcript_segment import TranscriptSegment
    from app.models.video_note import VideoNote


class Video(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "videos"
    __table_args__ = (
        UniqueConstraint("space_id", "url", name="uq_videos_space_url"),
        Index("ix_videos_space_order", "space_id", "order_index"),
        Index("ix_videos_space_completed", "space_id", "completed"),
        Index("ix_videos_source_id", "source_id"),
        Index("ix_videos_url", "url"),
    )

    title: Mapped[str] = mapped_column(String(220), nullable=False)
    thumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(160), nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_status: Mapped[str] = mapped_column(String(40), nullable=False, default="completed")
    transcript_status: Mapped[str] = mapped_column(String(40), nullable=False, default="pending")
    processing_status: Mapped[str] = mapped_column(String(40), nullable=False, default="completed")
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )

    space: Mapped[LearningSpace] = relationship(back_populates="videos")
    source: Mapped[Source | None] = relationship(back_populates="videos")
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="TranscriptSegment.order_index",
    )
    transcript_jobs: Mapped[list[TranscriptJob]] = relationship(
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    ai_summary: Mapped[object | None] = relationship(
        "AISummary",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
        primaryjoin="Video.id == foreign(AISummary.video_id)",
    )
    ai_summary_jobs: Mapped[list[object]] = relationship(
        "AISummaryJob",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    key_concepts: Mapped[list[object]] = relationship(
        "KeyConcept",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="desc(KeyConcept.relevance_score)",
    )
    key_takeaways: Mapped[list[object]] = relationship(
        "KeyTakeaway",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="KeyTakeaway.order_index",
    )
    review_questions: Mapped[list[object]] = relationship(
        "ReviewQuestion",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ReviewQuestion.order_index",
    )
    important_moments: Mapped[list[object]] = relationship(
        "ImportantMoment",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ImportantMoment.order_index",
    )
    notes: Mapped[list[object]] = relationship(
        "VideoNote",
        back_populates="video",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
