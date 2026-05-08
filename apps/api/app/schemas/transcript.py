from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TranscriptJobCreate(BaseModel):
    force: bool = False


class TranscriptSegmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    start_time: float
    end_time: float
    text: str
    order_index: int
    created_at: datetime


class TranscriptJobRead(BaseModel):
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


class VideoTranscriptRead(BaseModel):
    video_id: UUID
    status: str
    segments: list[TranscriptSegmentRead]
    job: TranscriptJobRead | None = None
    error_message: str | None = None
