from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class ExtensionSpaceRead(BaseModel):
    id: UUID
    title: str
    topic: str | None
    progress: int
    video_count: int
    updated_at: datetime


class ExtensionSaveRequest(BaseModel):
    space_id: UUID
    url: HttpUrl
    page_title: str | None = Field(default=None, max_length=220)
    page_description: str | None = Field(default=None, max_length=500)
    browser: str | None = Field(default=None, max_length=40)
    extension_version: str | None = Field(default=None, max_length=40)


class ExtensionSaveAccepted(BaseModel):
    save_id: UUID
    job_id: UUID
    source_id: UUID
    status: str
    platform: str
    source_type: str
    normalized_url: str
    message: str


class ExtensionRecentSaveRead(BaseModel):
    id: UUID
    space_id: UUID
    space_title: str
    source_id: UUID | None
    job_id: UUID | None
    url: str
    normalized_url: str
    platform: str
    source_type: str
    status: str
    error_message: str | None
    page_title: str | None
    created_at: datetime
    open_path: str