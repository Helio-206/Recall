from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.video import VideoRead

DifficultyLevel = Literal["Beginner", "Intermediate", "Advanced"]


class CurriculumReconstructionRequest(BaseModel):
    force: bool = False


class CurriculumManualOverrideUpdate(BaseModel):
    module_title: str | None = Field(default=None, min_length=1, max_length=180)
    order_index: int | None = Field(default=None, ge=0)
    locked: bool = True


class CurriculumReconstructionJobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    space_id: UUID
    status: str
    provider: str
    model: str
    prompt_version: str
    payload: dict[str, Any]
    error_message: str | None
    attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime


class VideoCurriculumProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    primary_topic: str
    subtopics: list[str] = Field(default_factory=list)
    difficulty_level: DifficultyLevel
    prerequisite_topics: list[str] = Field(default_factory=list)
    extracted_keywords: list[str] = Field(default_factory=list)
    module_hint: str | None
    redundancy_signals: list[str] = Field(default_factory=list)
    estimated_sequence_score: float
    confidence_score: float
    rationale: str | None
    provider: str
    model: str
    prompt_version: str
    manual_module_title: str | None
    manual_order_index: int | None
    manual_override_locked: bool


class VideoDependencyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    prerequisite_video_id: UUID
    dependent_video_id: UUID
    dependency_type: str
    rationale: str | None
    confidence_score: float


class ModuleVideoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    video_id: UUID
    order_index: int
    rationale: str | None
    confidence_score: float
    is_manual_override: bool
    video: VideoRead


class LearningModuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    order_index: int
    difficulty_level: DifficultyLevel
    learning_objectives: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None
    rationale: str | None
    confidence_score: float
    video_count: int = 0
    completed_count: int = 0
    progress: int = 0
    module_videos: list[ModuleVideoRead] = Field(default_factory=list)


class SuggestedNextVideoRead(BaseModel):
    video_id: UUID
    module_id: UUID
    title: str
    module_title: str
    reason: str
    difficulty_level: DifficultyLevel


class CurriculumHealthRead(BaseModel):
    score: int
    missing_transcript_count: int
    dependency_count: int
    duplicate_topic_count: int
    advanced_without_foundations_count: int
    manual_override_count: int
    unassigned_video_count: int
    warnings: list[str] = Field(default_factory=list)
    generated_at: datetime | None = None


class SpaceCurriculumRead(BaseModel):
    space_id: UUID
    modules: list[LearningModuleRead] = Field(default_factory=list)
    profiles: list[VideoCurriculumProfileRead] = Field(default_factory=list)
    dependencies: list[VideoDependencyRead] = Field(default_factory=list)
    suggested_next_video: SuggestedNextVideoRead | None = None
    health: CurriculumHealthRead
    latest_job: CurriculumReconstructionJobRead | None = None