from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

SearchKind = Literal["all", "transcript", "note", "summary", "concept", "important_moment"]


class SearchQueryCreate(BaseModel):
    query: str = Field(min_length=1, max_length=220)


class SearchQueryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: str
    last_used_at: datetime
    use_count: int


class SearchClickCreate(BaseModel):
    query: str = Field(min_length=1, max_length=220)
    result_kind: str = Field(min_length=1, max_length=40)
    result_id: str = Field(min_length=1, max_length=120)
    space_id: UUID | None = None
    video_id: UUID | None = None
    timestamp: float | None = None


class SearchClickRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: str
    result_kind: str
    result_id: str
    space_id: UUID | None
    video_id: UUID | None
    timestamp: float | None
    created_at: datetime


class SearchResultRead(BaseModel):
    id: str
    kind: SearchKind
    video_id: UUID
    video_title: str
    space_id: UUID
    space_title: str
    timestamp: float | None
    title: str
    excerpt: str
    highlighted_excerpt: str
    target_tab: Literal["transcript", "ai-summary", "notes"]
    relevance_score: float


class SearchResponse(BaseModel):
    query: str
    kind: SearchKind
    page: int
    per_page: int
    total: int
    hits: list[SearchResultRead]