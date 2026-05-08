from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VideoNoteUpsert(BaseModel):
    title: str | None = Field(default=None, max_length=180)
    content: str = Field(default="", max_length=12000)
    anchor_timestamp: float | None = Field(default=None, ge=0)


class VideoNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    video_id: UUID
    title: str | None
    content: str
    anchor_timestamp: float | None
    created_at: datetime
    updated_at: datetime