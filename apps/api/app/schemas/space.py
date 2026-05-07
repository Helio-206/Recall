from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.video import VideoRead


class LearningSpaceCreate(BaseModel):
    title: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    topic: str | None = Field(default=None, max_length=120)


class LearningSpaceUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    topic: str | None = Field(default=None, max_length=120)


class LearningSpaceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    topic: str | None
    created_at: datetime
    updated_at: datetime
    user_id: UUID
    progress: int = 0
    video_count: int = 0
    completed_count: int = 0


class LearningSpaceDetail(LearningSpaceRead):
    videos: list[VideoRead] = Field(default_factory=list)
