from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.statuses import PENDING
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.learning_module import LearningModule
    from app.models.space import LearningSpace


class CurriculumReconstructionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "curriculum_reconstruction_jobs"
    __table_args__ = (
        Index("ix_curriculum_reconstruction_jobs_user_id", "user_id"),
        Index("ix_curriculum_reconstruction_jobs_space_id", "space_id"),
        Index("ix_curriculum_reconstruction_jobs_status", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    space_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=PENDING)
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="heuristic")
    model: Mapped[str] = mapped_column(String(160), nullable=False, default="heuristic")
    prompt_version: Mapped[str] = mapped_column(String(40), nullable=False, default="v1")
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    space: Mapped[LearningSpace] = relationship(back_populates="curriculum_jobs")
    generated_modules: Mapped[list[LearningModule]] = relationship(
        back_populates="reconstruction_job"
    )