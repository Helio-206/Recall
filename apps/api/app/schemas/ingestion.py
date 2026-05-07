from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class IngestionRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=220)


class IngestionAccepted(BaseModel):
    job_id: UUID
    source_id: UUID
    status: str


class IngestionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    space_id: UUID
    source_id: UUID
    type: str
    status: str
    payload: dict[str, Any]
    error_message: str | None
    attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
