from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.space import LearningSpace
    from app.models.user import User
    from app.models.video import Video


class SearchResultClick(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "search_result_clicks"
    __table_args__ = (
        Index("ix_search_result_clicks_user_id", "user_id"),
        Index("ix_search_result_clicks_result_kind", "result_kind"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    query: Mapped[str] = mapped_column(String(220), nullable=False)
    result_kind: Mapped[str] = mapped_column(String(40), nullable=False)
    result_id: Mapped[str] = mapped_column(String(120), nullable=False)
    space_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("learning_spaces.id", ondelete="SET NULL"),
        nullable=True,
    )
    video_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="SET NULL"),
        nullable=True,
    )
    timestamp: Mapped[float | None] = mapped_column(Float, nullable=True)

    user: Mapped[User] = relationship(back_populates="search_result_clicks")
    space: Mapped[LearningSpace | None] = relationship()
    video: Mapped[Video | None] = relationship()