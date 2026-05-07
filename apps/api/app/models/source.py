from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.statuses import PENDING
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.ingestion_job import IngestionJob
    from app.models.space import LearningSpace
    from app.models.video import Video


class Source(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sources"
    __table_args__ = (
        Index("ix_sources_user_id", "user_id"),
        Index("ix_sources_space_id", "space_id"),
        Index("ix_sources_status", "status"),
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
    url: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(40), nullable=False, default="youtube")
    source_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    author: Mapped[str | None] = mapped_column(String(180), nullable=True)
    thumbnail: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default=PENDING)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    space: Mapped[LearningSpace] = relationship(back_populates="sources")
    videos: Mapped[list[Video]] = relationship(back_populates="source")
    jobs: Mapped[list[IngestionJob]] = relationship(
        back_populates="source",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
