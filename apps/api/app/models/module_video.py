from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learning_module import LearningModule
    from app.models.video import Video


class ModuleVideo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "module_videos"
    __table_args__ = (
        UniqueConstraint("module_id", "video_id", name="uq_module_videos_module_video"),
        UniqueConstraint("module_id", "order_index", name="uq_module_videos_module_order"),
        Index("ix_module_videos_module_id", "module_id"),
        Index("ix_module_videos_video_id", "video_id"),
    )

    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_modules.id", ondelete="CASCADE"),
        nullable=False,
    )
    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    is_manual_override: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    module: Mapped[LearningModule] = relationship(back_populates="module_videos")
    video: Mapped[Video] = relationship(back_populates="module_entries")