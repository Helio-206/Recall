from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.curriculum_reconstruction_job import CurriculumReconstructionJob
    from app.models.module_video import ModuleVideo
    from app.models.space import LearningSpace


class LearningModule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_modules"
    __table_args__ = (
        UniqueConstraint("space_id", "order_index", name="uq_learning_modules_space_order"),
        Index("ix_learning_modules_space_id", "space_id"),
        Index("ix_learning_modules_space_difficulty", "space_id", "difficulty_level"),
        Index("ix_learning_modules_job_id", "reconstruction_job_id"),
    )

    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    reconstruction_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("curriculum_reconstruction_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty_level: Mapped[str] = mapped_column(String(24), nullable=False, default="Beginner")
    learning_objectives: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    estimated_duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    space: Mapped[LearningSpace] = relationship(back_populates="learning_modules")
    reconstruction_job: Mapped[CurriculumReconstructionJob | None] = relationship(
        back_populates="generated_modules"
    )
    module_videos: Mapped[list[ModuleVideo]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ModuleVideo.order_index",
    )