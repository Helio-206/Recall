from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    space_id: UUID
    url: str
    platform: str
    source_type: str
    title: str | None
    author: str | None
    thumbnail: str | None
    duration: int | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
