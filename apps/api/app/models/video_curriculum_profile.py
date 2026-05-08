from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.space import LearningSpace
    from app.models.video import Video


class VideoCurriculumProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_curriculum_profiles"
    __table_args__ = (
        UniqueConstraint("video_id", name="uq_video_curriculum_profiles_video_id"),
        Index("ix_video_curriculum_profiles_space_id", "space_id"),
        Index("ix_video_curriculum_profiles_primary_topic", "primary_topic"),
        Index("ix_video_curriculum_profiles_difficulty", "difficulty_level"),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    primary_topic: Mapped[str] = mapped_column(String(180), nullable=False)
    subtopics: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    difficulty_level: Mapped[str] = mapped_column(String(24), nullable=False, default="Beginner")
    prerequisite_topics: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    extracted_keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    module_hint: Mapped[str | None] = mapped_column(String(180), nullable=True)
    redundancy_signals: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    estimated_sequence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="heuristic")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="heuristic")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1")
    manual_module_title: Mapped[str | None] = mapped_column(String(180), nullable=True)
    manual_order_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    manual_override_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    space: Mapped[LearningSpace] = relationship(back_populates="curriculum_profiles")
    video: Mapped[Video] = relationship(back_populates="curriculum_profile")