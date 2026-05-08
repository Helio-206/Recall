from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.video import Video


class KeyConcept(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "key_concepts"

    video_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept: Mapped[str] = mapped_column(String(220), nullable=False)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    video: Mapped[Video] = relationship(back_populates="key_concepts")