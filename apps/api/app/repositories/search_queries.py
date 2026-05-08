from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.search_query import SearchQuery
from app.models.search_result_click import SearchResultClick


class SearchQueryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_recent(self, *, user_id: UUID, limit: int = 8) -> list[SearchQuery]:
        stmt = (
            select(SearchQuery)
            .where(SearchQuery.user_id == user_id)
            .order_by(SearchQuery.last_used_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def get_by_query(self, *, user_id: UUID, query: str) -> SearchQuery | None:
        stmt = select(SearchQuery).where(SearchQuery.user_id == user_id, SearchQuery.query == query)
        return self.db.scalar(stmt)

    def touch(self, *, user_id: UUID, query: str) -> SearchQuery:
        existing = self.get_by_query(user_id=user_id, query=query)
        now = datetime.now(UTC)
        if existing:
            existing.last_used_at = now
            existing.use_count += 1
            self.db.flush()
            return existing

        record = SearchQuery(user_id=user_id, query=query, last_used_at=now, use_count=1)
        self.db.add(record)
        self.db.flush()
        return record

    def create_click(
        self,
        *,
        user_id: UUID,
        query: str,
        result_kind: str,
        result_id: str,
        space_id: UUID | None,
        video_id: UUID | None,
        timestamp: float | None,
    ) -> SearchResultClick:
        click = SearchResultClick(
            user_id=user_id,
            query=query,
            result_kind=result_kind,
            result_id=result_id,
            space_id=space_id,
            video_id=video_id,
            timestamp=timestamp,
        )
        self.db.add(click)
        self.db.flush()
        return click