from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.source import Source
    from app.models.user import User
    from app.models.video import Video


class LearningSpace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "learning_spaces"
    __table_args__ = (
        Index("ix_learning_spaces_user_created", "user_id", "created_at"),
        Index("ix_learning_spaces_user_topic", "user_id", "topic"),
    )

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    topic: Mapped[str | None] = mapped_column(String(120), nullable=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="spaces")
    sources: Mapped[list[Source]] = relationship(
        back_populates="space",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    videos: Mapped[list[Video]] = relationship(
        back_populates="space",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Video.order_index",
    )
