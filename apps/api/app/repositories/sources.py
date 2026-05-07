from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.source import Source


class SourceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        space_id: UUID,
        url: str,
        platform: str,
        source_type: str,
        title: str | None = None,
    ) -> Source:
        source = Source(
            user_id=user_id,
            space_id=space_id,
            url=url,
            platform=platform,
            source_type=source_type,
            title=title,
        )
        self.db.add(source)
        self.db.flush()
        return source

    def get(self, source_id: UUID) -> Source | None:
        return self.db.get(Source, source_id)

    def list_for_space(self, *, space_id: UUID, user_id: UUID) -> list[Source]:
        stmt = (
            select(Source)
            .where(Source.space_id == space_id, Source.user_id == user_id)
            .order_by(Source.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def set_status(
        self,
        source: Source,
        *,
        status: str,
        error_message: str | None = None,
    ) -> Source:
        source.status = status
        source.error_message = error_message
        self.db.flush()
        return source
