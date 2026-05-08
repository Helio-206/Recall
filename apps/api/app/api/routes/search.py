from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.search import (
    SearchClickCreate,
    SearchClickRead,
    SearchQueryCreate,
    SearchQueryRead,
    SearchResponse,
)
from app.services.search import SearchService

router = APIRouter()


@router.get("", response_model=SearchResponse)
def search_learning_content(
    q: str = Query(default="", min_length=0, max_length=220),
    kind: str | None = Query(default=None),
    space_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=8, ge=1, le=25),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    return SearchService(db).search(
        query=q,
        user_id=current_user.id,
        kind=kind,
        space_id=space_id,
        page=page,
        per_page=per_page,
    )


@router.get("/recent", response_model=list[SearchQueryRead])
def get_recent_searches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SearchQueryRead]:
    return SearchService(db).list_recent_queries(user_id=current_user.id)


@router.post("/recent", response_model=SearchQueryRead, status_code=status.HTTP_201_CREATED)
def save_recent_search(
    payload: SearchQueryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchQueryRead:
    return SearchService(db).save_recent_query(user_id=current_user.id, payload=payload)


@router.post("/clicks", response_model=SearchClickRead, status_code=status.HTTP_201_CREATED)
def record_search_click(
    payload: SearchClickCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SearchClickRead:
    return SearchService(db).record_click(user_id=current_user.id, payload=payload)