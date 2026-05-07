from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class VideoCreate(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=220)


class VideoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=220)
    order_index: int | None = Field(default=None, ge=0)
    completed: bool | None = None


class VideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    thumbnail: str | None
    author: str | None
    duration: int | None
    url: str
    order_index: int
    completed: bool
    space_id: UUID
    source_id: UUID | None
    metadata_status: str
    transcript_status: str
    processing_status: str
    created_at: datetime
    updated_at: datetime
