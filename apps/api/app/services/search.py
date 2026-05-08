from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories.search_queries import SearchQueryRepository
from app.schemas.search import (
    SearchClickCreate,
    SearchClickRead,
    SearchQueryCreate,
    SearchQueryRead,
    SearchResponse,
    SearchResultRead,
)
from app.services.search_backend import SearchBackendUnavailable, get_search_backend


class SearchService:
    VALID_KINDS = {"all", "transcript", "note", "summary", "concept", "important_moment"}

    def __init__(self, db: Session) -> None:
        self.db = db
        self.history = SearchQueryRepository(db)

    def search(
        self,
        *,
        query: str,
        user_id: UUID,
        kind: str | None,
        space_id: UUID | None,
        page: int,
        per_page: int,
    ) -> SearchResponse:
        normalized_query = query.strip()
        resolved_kind = kind if kind in self.VALID_KINDS else "all"
        if not normalized_query:
            return SearchResponse(
                query="",
                kind=resolved_kind,
                page=page,
                per_page=per_page,
                total=0,
                hits=[],
            )

        filters = [f'user_id = "{user_id}"']
        if resolved_kind != "all":
            filters.append(f'kind = "{resolved_kind}"')
        if space_id:
            filters.append(f'space_id = "{space_id}"')

        backend = get_search_backend()
        try:
            payload = backend.search(
                query=normalized_query,
                filter_expression=" AND ".join(filters),
                offset=(page - 1) * per_page,
                limit=per_page,
            )
        except SearchBackendUnavailable as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Search is temporarily unavailable.",
            ) from exc

        hits = [self._serialize_hit(hit) for hit in payload.get("hits", [])]
        return SearchResponse(
            query=normalized_query,
            kind=resolved_kind,
            page=page,
            per_page=per_page,
            total=int(payload.get("estimatedTotalHits") or 0),
            hits=hits,
        )

    def list_recent_queries(self, *, user_id: UUID) -> list[SearchQueryRead]:
        return [
            SearchQueryRead.model_validate(item)
            for item in self.history.list_recent(user_id=user_id)
        ]

    def save_recent_query(self, *, user_id: UUID, payload: SearchQueryCreate) -> SearchQueryRead:
        query_text = payload.query.strip()
        if not query_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Query is required.",
            )
        record = self.history.touch(user_id=user_id, query=query_text)
        self.db.commit()
        self.db.refresh(record)
        return SearchQueryRead.model_validate(record)

    def record_click(self, *, user_id: UUID, payload: SearchClickCreate) -> SearchClickRead:
        click = self.history.create_click(
            user_id=user_id,
            query=payload.query.strip(),
            result_kind=payload.result_kind,
            result_id=payload.result_id,
            space_id=payload.space_id,
            video_id=payload.video_id,
            timestamp=payload.timestamp,
        )
        self.db.commit()
        self.db.refresh(click)
        return SearchClickRead.model_validate(click)

    def _serialize_hit(self, hit: dict[str, object]) -> SearchResultRead:
        formatted = hit.get("_formatted") if isinstance(hit.get("_formatted"), dict) else {}
        formatted = formatted if isinstance(formatted, dict) else {}
        excerpt = str(hit.get("content") or "")
        highlighted_excerpt = str(formatted.get("content") or excerpt)
        if len(excerpt) > 280:
            excerpt = excerpt[:279].rstrip() + "..."
        if len(highlighted_excerpt) > 360:
            highlighted_excerpt = highlighted_excerpt[:359].rstrip() + "..."

        return SearchResultRead(
            id=str(hit.get("id")),
            kind=str(hit.get("kind") or "all"),
            video_id=UUID(str(hit.get("video_id"))),
            video_title=str(
                formatted.get("video_title") or hit.get("video_title") or "Untitled video"
            ),
            space_id=UUID(str(hit.get("space_id"))),
            space_title=str(
                formatted.get("space_title") or hit.get("space_title") or "Learning space"
            ),
            timestamp=float(hit.get("timestamp") or 0),
            title=str(
                formatted.get("title") or hit.get("title") or hit.get("video_title") or "Match"
            ),
            excerpt=excerpt,
            highlighted_excerpt=highlighted_excerpt,
            target_tab=str(hit.get("target_tab") or "transcript"),
            relevance_score=float(hit.get("_rankingScore") or 0),
        )