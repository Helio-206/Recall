from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.space import LearningSpace
    from app.models.video import Video


class VideoDependency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "video_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "prerequisite_video_id",
            "dependent_video_id",
            name="uq_video_dependencies_edge",
        ),
        Index("ix_video_dependencies_space_id", "space_id"),
        Index("ix_video_dependencies_prerequisite", "prerequisite_video_id"),
        Index("ix_video_dependencies_dependent", "dependent_video_id"),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    prerequisite_video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependent_video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    dependency_type: Mapped[str] = mapped_column(String(40), nullable=False, default="concept")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    space: Mapped[LearningSpace] = relationship(back_populates="video_dependencies")
    prerequisite_video: Mapped[Video] = relationship(
        back_populates="dependent_edges",
        foreign_keys=[prerequisite_video_id],
    )
    dependent_video: Mapped[Video] = relationship(
        back_populates="prerequisite_edges",
        foreign_keys=[dependent_video_id],
    )