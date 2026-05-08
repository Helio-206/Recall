from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AISummaryJobCreate(BaseModel):
    force: bool = False


class AISummaryJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    video_id: UUID
    status: str
    payload: dict[str, Any]
    error_message: str | None
    attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class KeyConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    concept: str
    relevance_score: float


class KeyTakeawayRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    content: str
    order_index: int


class ReviewQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    question: str
    answer: str
    order_index: int


class ImportantMomentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    title: str
    timestamp: float
    description: str
    order_index: int


class AISummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    short_summary: str | None
    detailed_summary: str | None
    learning_notes: str | None
    status: str
    prompt_version: str
    created_at: datetime
    updated_at: datetime


class VideoLearningInsightsRead(BaseModel):
    video_id: UUID
    status: str
    summary: AISummaryRead | None = None
    key_concepts: list[KeyConceptRead]
    key_takeaways: list[KeyTakeawayRead]
    review_questions: list[ReviewQuestionRead]
    important_moments: list[ImportantMomentRead]
    job: AISummaryJobRead | None = None
    error_message: str | None = None