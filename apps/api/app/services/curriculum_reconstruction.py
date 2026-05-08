from __future__ import annotations

import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from redis import Redis
from rq import Queue, Retry
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.statuses import COMPLETED, FAILED
from app.models.curriculum_reconstruction_job import CurriculumReconstructionJob
from app.models.learning_module import LearningModule
from app.models.module_video import ModuleVideo
from app.models.space import LearningSpace
from app.models.video import Video
from app.models.video_curriculum_profile import VideoCurriculumProfile
from app.models.video_dependency import VideoDependency
from app.repositories.curriculum_reconstruction_jobs import CurriculumReconstructionJobRepository
from app.schemas.curriculum import (
    CurriculumHealthRead,
    CurriculumManualOverrideUpdate,
    CurriculumReconstructionJobRead,
    CurriculumReconstructionRequest,
    LearningModuleRead,
    ModuleVideoRead,
    SpaceCurriculumRead,
    SuggestedNextVideoRead,
    VideoCurriculumProfileRead,
    VideoDependencyRead,
)
from app.schemas.video import VideoRead
from app.services.curriculum_provider import (
    CurriculumProfileDraft,
    CurriculumProviderResult,
    build_video_contexts,
    get_curriculum_provider,
    resolve_curriculum_provider_name,
)
from app.services.search_indexing import sync_space_search_documents

DIFFICULTY_ORDER = {"Beginner": 0, "Intermediate": 1, "Advanced": 2}


@dataclass(slots=True)
class _DependencyPlan:
    prerequisite_video_id: UUID
    dependent_video_id: UUID
    dependency_type: str
    rationale: str
    confidence_score: float


@dataclass(slots=True)
class _ModuleVideoPlan:
    video: Video
    order_index: int
    rationale: str
    confidence_score: float
    is_manual_override: bool


@dataclass(slots=True)
class _ModulePlan:
    title: str
    description: str | None
    order_index: int
    difficulty_level: str
    learning_objectives: list[str]
    estimated_duration_minutes: int | None
    rationale: str | None
    confidence_score: float
    videos: list[_ModuleVideoPlan]


class CurriculumReconstructionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.jobs = CurriculumReconstructionJobRepository(db)

    def get_curriculum(self, *, space_id: UUID, user_id: UUID) -> SpaceCurriculumRead:
        space = self._get_space(space_id=space_id, user_id=user_id, include_curriculum=True)
        return self._serialize_curriculum(space)

    def request_rebuild(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
        payload: CurriculumReconstructionRequest,
    ) -> CurriculumReconstructionJobRead:
        space = self._get_space(space_id=space_id, user_id=user_id, include_curriculum=False)
        if not space.videos:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Add videos before reconstructing the curriculum.",
            )

        active_job = self.jobs.active_for_space(space_id=space_id, user_id=user_id)
        if active_job and not payload.force:
            return CurriculumReconstructionJobRead.model_validate(active_job)

        provider_name = resolve_curriculum_provider_name(self.settings)
        provider_model = (
            self.settings.ollama_model
            if provider_name == "ollama"
            else self.settings.openrouter_model
            if provider_name == "openrouter"
            else "heuristic"
        )

        job = self.jobs.create(
            user_id=user_id,
            space_id=space.id,
            provider=provider_name,
            model=provider_model,
            prompt_version=self.settings.curriculum_prompt_version,
            payload={
                "phase": "queued",
                "video_count": len(space.videos),
                "space_title": space.title,
                "provider": provider_name,
                "model": provider_model,
            },
        )
        self.db.commit()
        self.db.refresh(job)

        if provider_name == "heuristic":
            try:
                self.process_job(job_id=job.id)
            except Exception:
                pass
            refreshed = self.jobs.get(job.id)
            return CurriculumReconstructionJobRead.model_validate(refreshed or job)

        try:
            self._queue().enqueue(
                "app.workers.curriculum_reconstruction_worker.process_curriculum_reconstruction_job",
                str(job.id),
                job_timeout=self.settings.curriculum_job_timeout_seconds,
                retry=Retry(max=self.settings.curriculum_retry_attempts, interval=[120]),
            )
        except Exception:
            self.jobs.set_status(
                job,
                status=FAILED,
                error_message="Curriculum worker is unavailable.",
                payload=merge_payload(job.payload, phase="failed"),
                finished_at=datetime.now(UTC),
            )
            self.db.commit()
        return CurriculumReconstructionJobRead.model_validate(job)

    def get_job_for_user(self, *, job_id: UUID, user_id: UUID) -> CurriculumReconstructionJobRead:
        job = self.jobs.get_for_user(job_id=job_id, user_id=user_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Curriculum reconstruction job not found.",
            )
        return CurriculumReconstructionJobRead.model_validate(job)

    def update_manual_override(
        self,
        *,
        space_id: UUID,
        video_id: UUID,
        user_id: UUID,
        payload: CurriculumManualOverrideUpdate,
    ) -> SpaceCurriculumRead:
        space = self._get_space(space_id=space_id, user_id=user_id, include_curriculum=True)
        video = next((item for item in space.videos if item.id == video_id), None)
        if not video:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found.")

        profile = video.curriculum_profile
        if profile is None:
            profile = VideoCurriculumProfile(
                space_id=space.id,
                video_id=video.id,
                primary_topic=video.title,
                difficulty_level="Intermediate",
                prerequisite_topics=[],
                subtopics=[],
                extracted_keywords=[],
                redundancy_signals=[],
                estimated_sequence_score=float(video.order_index),
                confidence_score=0.0,
                provider="manual",
                model="manual",
                prompt_version=self.settings.curriculum_prompt_version,
            )
            self.db.add(profile)

        current_module_title = None
        for module in space.learning_modules:
            for entry in module.module_videos:
                if entry.video_id == video.id:
                    current_module_title = module.title
                    break
            if current_module_title:
                break

        profile.manual_module_title = (
            payload.module_title.strip()
            if payload.module_title
            else current_module_title if payload.locked else None
        )
        profile.manual_order_index = payload.order_index if payload.locked else None
        profile.manual_override_locked = payload.locked
        self.db.commit()
        return self.get_curriculum(space_id=space_id, user_id=user_id)

    def process_job(self, *, job_id: UUID) -> None:
        job = self.jobs.get(job_id)
        if not job:
            return

        space = self._get_space(
            space_id=job.space_id,
            user_id=job.user_id,
            include_curriculum=True,
        )
        if not space.videos:
            raise ValueError("The learning space has no videos to reconstruct.")

        started_at = datetime.now(UTC)
        self.jobs.mark_processing(job, started_at=started_at)
        job.payload = merge_payload(job.payload, phase="analyzing_videos")
        self.db.commit()

        contexts = build_video_contexts(space.videos)
        provider = get_curriculum_provider(prompt_version=self.settings.curriculum_prompt_version)
        analysis = provider.analyze_videos(space=space, contexts=contexts)

        profile_map = self._upsert_profiles(space=space, analysis=analysis)
        dependencies = self._build_dependency_plans(space=space, profile_map=profile_map)
        modules = self._build_module_plans(
            space=space,
            profile_map=profile_map,
            dependencies=dependencies,
        )

        self._replace_dependencies(space=space, dependencies=dependencies)
        self._replace_modules(space=space, job=job, modules=modules)
        space.updated_at = datetime.now(UTC)

        self.jobs.set_status(
            job,
            status=COMPLETED,
            provider=analysis.provider,
            model=analysis.model,
            payload=merge_payload(
                job.payload,
                phase="completed",
                provider=analysis.provider,
                model=analysis.model,
                request_count=analysis.request_count,
                batch_count=analysis.batch_count,
                usage=analysis.usage,
            ),
            finished_at=datetime.now(UTC),
        )
        self.db.commit()
        sync_space_search_documents(self.db, space_id=space.id)

    def _get_space(
        self,
        *,
        space_id: UUID,
        user_id: UUID,
        include_curriculum: bool,
    ) -> LearningSpace:
        stmt = (
            select(LearningSpace)
            .where(LearningSpace.id == space_id, LearningSpace.user_id == user_id)
            .options(
                selectinload(LearningSpace.videos).selectinload(Video.transcript_segments),
                selectinload(LearningSpace.videos).selectinload(Video.ai_summary),
                selectinload(LearningSpace.videos).selectinload(Video.key_concepts),
                selectinload(LearningSpace.videos).selectinload(Video.notes),
                selectinload(LearningSpace.videos).selectinload(Video.curriculum_profile),
            )
        )
        if include_curriculum:
            stmt = stmt.options(
                selectinload(LearningSpace.learning_modules)
                .selectinload(LearningModule.module_videos)
                .selectinload(ModuleVideo.video),
                selectinload(LearningSpace.video_dependencies),
                selectinload(LearningSpace.curriculum_jobs),
            )
        space = self.db.scalar(stmt)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )
        return space

    def _upsert_profiles(
        self,
        *,
        space: LearningSpace,
        analysis: CurriculumProviderResult,
    ) -> dict[UUID, VideoCurriculumProfile]:
        draft_by_video_id = {UUID(draft.video_id): draft for draft in analysis.profiles}
        existing_profiles = {
            video.curriculum_profile.video_id: video.curriculum_profile
            for video in space.videos
            if video.curriculum_profile is not None
        }
        profile_map: dict[UUID, VideoCurriculumProfile] = {}

        for video in sorted(space.videos, key=lambda item: item.order_index):
            draft = draft_by_video_id.get(video.id) or self._fallback_profile(video)
            profile = existing_profiles.get(video.id)
            if profile is None:
                profile = VideoCurriculumProfile(space_id=space.id, video_id=video.id)
                self.db.add(profile)

            profile.primary_topic = draft.primary_topic
            profile.subtopics = draft.subtopics
            profile.difficulty_level = draft.difficulty_level
            profile.prerequisite_topics = draft.prerequisite_topics
            profile.extracted_keywords = draft.extracted_keywords
            profile.module_hint = draft.module_hint
            profile.redundancy_signals = []
            profile.estimated_sequence_score = draft.estimated_sequence_score
            profile.confidence_score = draft.confidence_score
            profile.rationale = draft.rationale
            profile.provider = analysis.provider
            profile.model = analysis.model
            profile.prompt_version = self.settings.curriculum_prompt_version
            profile_map[video.id] = profile

        self.db.flush()
        self._tag_redundancy_signals(space=space, profile_map=profile_map)
        return profile_map

    def _build_dependency_plans(
        self,
        *,
        space: LearningSpace,
        profile_map: dict[UUID, VideoCurriculumProfile],
    ) -> list[_DependencyPlan]:
        ordered_videos = sorted(space.videos, key=lambda item: item.order_index)
        topic_index = defaultdict(list)
        for video in ordered_videos:
            profile = profile_map[video.id]
            for token in _profile_tokens(profile):
                topic_index[token].append(video)

        dependencies: dict[tuple[UUID, UUID], _DependencyPlan] = {}
        for index, video in enumerate(ordered_videos):
            profile = profile_map[video.id]
            for topic in profile.prerequisite_topics:
                prerequisite = self._find_prerequisite_candidate(
                    ordered_videos=ordered_videos[:index],
                    candidates=topic_index[_normalize_token(topic)],
                    dependent_video=video,
                    dependent_profile=profile,
                )
                if prerequisite is None:
                    continue
                key = (prerequisite.id, video.id)
                dependencies[key] = _DependencyPlan(
                    prerequisite_video_id=prerequisite.id,
                    dependent_video_id=video.id,
                    dependency_type="topic_foundation",
                    rationale=f"{prerequisite.title} introduces concepts reused in {video.title}.",
                    confidence_score=0.66,
                )

            if index > 0 and not any(
                plan.dependent_video_id == video.id for plan in dependencies.values()
            ):
                previous = ordered_videos[index - 1]
                if _difficulty_weight(profile_map[previous.id]) <= _difficulty_weight(profile):
                    key = (previous.id, video.id)
                    dependencies[key] = _DependencyPlan(
                        prerequisite_video_id=previous.id,
                        dependent_video_id=video.id,
                        dependency_type="sequence",
                        rationale=f"{video.title} is easier to follow after {previous.title}.",
                        confidence_score=0.45,
                    )

        return list(dependencies.values())

    def _build_module_plans(
        self,
        *,
        space: LearningSpace,
        profile_map: dict[UUID, VideoCurriculumProfile],
        dependencies: list[_DependencyPlan],
    ) -> list[_ModulePlan]:
        buckets: dict[str, list[Video]] = defaultdict(list)
        for video in sorted(space.videos, key=lambda item: item.order_index):
            profile = profile_map[video.id]
            module_key = self._module_key(profile=profile, video=video)
            buckets[module_key].append(video)

        module_names = list(buckets)
        module_edges: dict[str, set[str]] = {name: set() for name in module_names}
        video_to_module = {
            video.id: module_name for module_name, videos in buckets.items() for video in videos
        }
        for dependency in dependencies:
            source_module = video_to_module[dependency.prerequisite_video_id]
            target_module = video_to_module[dependency.dependent_video_id]
            if source_module != target_module:
                module_edges[target_module].add(source_module)

        ordered_modules = _stable_topological_sort(
            nodes=module_names,
            edges=module_edges,
            sort_key=lambda item: min(video.order_index for video in buckets[item]),
        )

        plans: list[_ModulePlan] = []
        for module_index, module_name in enumerate(ordered_modules):
            module_videos = buckets[module_name]
            ordered_videos = self._order_module_videos(
                videos=module_videos,
                profile_map=profile_map,
                dependencies=dependencies,
            )
            profiles = [profile_map[video.id] for video in module_videos]
            module_title = self._module_title(module_name=module_name, videos=module_videos)
            plans.append(
                _ModulePlan(
                    title=module_title,
                    description=self._module_description(
                        module_title=module_title,
                        videos=module_videos,
                    ),
                    order_index=module_index,
                    difficulty_level=_module_difficulty(profiles),
                    learning_objectives=_module_objectives(profiles),
                    estimated_duration_minutes=_module_duration_minutes(module_videos),
                    rationale=self._module_rationale(
                        module_title=module_title,
                        videos=module_videos,
                    ),
                    confidence_score=round(
                        sum(profile.confidence_score for profile in profiles)
                        / max(len(profiles), 1),
                        2,
                    ),
                    videos=ordered_videos,
                )
            )
        return plans

    def _replace_dependencies(
        self,
        *,
        space: LearningSpace,
        dependencies: list[_DependencyPlan],
    ) -> None:
        self.db.execute(delete(VideoDependency).where(VideoDependency.space_id == space.id))
        self.db.flush()
        for plan in dependencies:
            self.db.add(
                VideoDependency(
                    space_id=space.id,
                    prerequisite_video_id=plan.prerequisite_video_id,
                    dependent_video_id=plan.dependent_video_id,
                    dependency_type=plan.dependency_type,
                    rationale=plan.rationale,
                    confidence_score=plan.confidence_score,
                )
            )
        self.db.flush()

    def _replace_modules(
        self,
        *,
        space: LearningSpace,
        job: CurriculumReconstructionJob,
        modules: list[_ModulePlan],
    ) -> None:
        self.db.execute(delete(LearningModule).where(LearningModule.space_id == space.id))
        self.db.flush()

        for module in modules:
            row = LearningModule(
                space_id=space.id,
                reconstruction_job_id=job.id,
                title=module.title,
                description=module.description,
                order_index=module.order_index,
                difficulty_level=module.difficulty_level,
                learning_objectives=module.learning_objectives,
                estimated_duration_minutes=module.estimated_duration_minutes,
                rationale=module.rationale,
                confidence_score=module.confidence_score,
            )
            self.db.add(row)
            self.db.flush()
            for plan in module.videos:
                self.db.add(
                    ModuleVideo(
                        module_id=row.id,
                        video_id=plan.video.id,
                        order_index=plan.order_index,
                        rationale=plan.rationale,
                        confidence_score=plan.confidence_score,
                        is_manual_override=plan.is_manual_override,
                    )
                )
        self.db.flush()

    def _order_module_videos(
        self,
        *,
        videos: list[Video],
        profile_map: dict[UUID, VideoCurriculumProfile],
        dependencies: list[_DependencyPlan],
    ) -> list[_ModuleVideoPlan]:
        ids = {video.id for video in videos}
        edges: dict[UUID, set[UUID]] = {video.id: set() for video in videos}
        for dependency in dependencies:
            if dependency.prerequisite_video_id in ids and dependency.dependent_video_id in ids:
                edges[dependency.dependent_video_id].add(dependency.prerequisite_video_id)

        ordered_ids = _stable_topological_sort(
            nodes=[video.id for video in videos],
            edges=edges,
            sort_key=lambda video_id: (
                profile_map[video_id].manual_order_index
                if profile_map[video_id].manual_override_locked
                and profile_map[video_id].manual_order_index is not None
                else 10_000,
                DIFFICULTY_ORDER[profile_map[video_id].difficulty_level],
                next(item.order_index for item in videos if item.id == video_id),
            ),
        )
        id_to_video = {video.id: video for video in videos}
        return [
            _ModuleVideoPlan(
                video=id_to_video[video_id],
                order_index=index,
                rationale=(
                    profile_map[video_id].rationale
                    or "Kept in a stable prerequisite-first order."
                ),
                confidence_score=profile_map[video_id].confidence_score,
                is_manual_override=profile_map[video_id].manual_override_locked,
            )
            for index, video_id in enumerate(ordered_ids)
        ]

    def _module_key(self, *, profile: VideoCurriculumProfile, video: Video) -> str:
        if profile.manual_override_locked and profile.manual_module_title:
            return profile.manual_module_title.strip()
        return (profile.module_hint or profile.primary_topic or video.title).strip()

    def _module_title(self, *, module_name: str, videos: list[Video]) -> str:
        title = module_name.strip()
        if title:
            return title
        return f"Module {min(video.order_index for video in videos) + 1}"

    def _module_description(self, *, module_title: str, videos: list[Video]) -> str:
        first = videos[0].title
        last = videos[-1].title
        if first == last:
            return f"Build confidence in {module_title} through {first}."
        return f"Progress from {first} to {last} while staying inside {module_title}."

    def _module_rationale(self, *, module_title: str, videos: list[Video]) -> str:
        return (
            f"Grouped {len(videos)} lessons into {module_title} "
            "based on topic overlap and depth."
        )

    def _find_prerequisite_candidate(
        self,
        *,
        ordered_videos: list[Video],
        candidates: list[Video],
        dependent_video: Video,
        dependent_profile: VideoCurriculumProfile,
    ) -> Video | None:
        candidate_ids = {video.id for video in candidates}
        filtered = [video for video in ordered_videos if video.id in candidate_ids]
        if not filtered:
            return None
        filtered.sort(
            key=lambda video: (
                DIFFICULTY_ORDER.get(video.curriculum_profile.difficulty_level, 1)
                if video.curriculum_profile
                else 1,
                video.order_index,
            )
        )
        for candidate in filtered:
            if candidate.id == dependent_video.id:
                continue
            if candidate.order_index <= dependent_video.order_index:
                return candidate
        return None

    def _fallback_profile(self, video: Video) -> CurriculumProfileDraft:
        return CurriculumProfileDraft(
            video_id=str(video.id),
            primary_topic=video.title,
            difficulty_level="Intermediate",
            extracted_keywords=[video.title],
            estimated_sequence_score=float(video.order_index),
            rationale="Fallback profile generated from the existing lesson metadata.",
            confidence_score=0.2,
        )

    def _tag_redundancy_signals(
        self,
        *,
        space: LearningSpace,
        profile_map: dict[UUID, VideoCurriculumProfile],
    ) -> None:
        topic_groups: dict[str, list[UUID]] = defaultdict(list)
        for video in space.videos:
            topic_groups[_normalize_token(profile_map[video.id].primary_topic)].append(video.id)
        for topic, video_ids in topic_groups.items():
            if len(video_ids) <= 1:
                continue
            for video_id in video_ids:
                profile_map[video_id].redundancy_signals = [f"Overlaps with other {topic} lessons."]

    def _serialize_curriculum(self, space: LearningSpace) -> SpaceCurriculumRead:
        latest_job = space.curriculum_jobs[0] if space.curriculum_jobs else None
        modules = [self._serialize_module(module) for module in space.learning_modules]
        profiles = [
            VideoCurriculumProfileRead.model_validate(video.curriculum_profile)
            for video in sorted(space.videos, key=lambda item: item.order_index)
            if video.curriculum_profile is not None
        ]
        dependencies = [
            VideoDependencyRead.model_validate(item) for item in space.video_dependencies
        ]
        health = self._build_health(
            space=space,
            modules=modules,
            profiles=profiles,
            dependencies=dependencies,
        )
        return SpaceCurriculumRead(
            space_id=space.id,
            modules=modules or [self._fallback_module(space)],
            profiles=profiles,
            dependencies=dependencies,
            suggested_next_video=self._suggest_next_video(space=space, modules=modules),
            health=health,
            latest_job=(
                CurriculumReconstructionJobRead.model_validate(latest_job)
                if latest_job
                else None
            ),
        )

    def _serialize_module(self, module: LearningModule) -> LearningModuleRead:
        ordered_entries = sorted(module.module_videos, key=lambda item: item.order_index)
        completed_count = sum(1 for entry in ordered_entries if entry.video.completed)
        video_count = len(ordered_entries)
        progress = round((completed_count / video_count) * 100) if video_count else 0
        return LearningModuleRead(
            id=module.id,
            title=module.title,
            description=module.description,
            order_index=module.order_index,
            difficulty_level=module.difficulty_level,
            learning_objectives=module.learning_objectives or [],
            estimated_duration_minutes=module.estimated_duration_minutes,
            rationale=module.rationale,
            confidence_score=module.confidence_score,
            video_count=video_count,
            completed_count=completed_count,
            progress=progress,
            module_videos=[
                ModuleVideoRead(
                    id=entry.id,
                    video_id=entry.video_id,
                    order_index=entry.order_index,
                    rationale=entry.rationale,
                    confidence_score=entry.confidence_score,
                    is_manual_override=entry.is_manual_override,
                    video=VideoRead.model_validate(entry.video),
                )
                for entry in ordered_entries
            ],
        )

    def _fallback_module(self, space: LearningSpace) -> LearningModuleRead:
        pseudo_id = uuid.uuid5(space.id, "fallback-curriculum")
        entries = []
        videos = sorted(space.videos, key=lambda item: item.order_index)
        for index, video in enumerate(videos):
            entries.append(
                ModuleVideoRead(
                    id=uuid.uuid5(video.id, "fallback-module-video"),
                    video_id=video.id,
                    order_index=index,
                    rationale=(
                        "Preserved original import order until the first reconstruction "
                        "job runs."
                    ),
                    confidence_score=0.0,
                    is_manual_override=False,
                    video=VideoRead.model_validate(video),
                )
            )
        completed_count = sum(1 for video in videos if video.completed)
        progress = round((completed_count / len(videos)) * 100) if videos else 0
        return LearningModuleRead(
            id=pseudo_id,
            title="Imported Sequence",
            description="Current ingest order before AI curriculum reconstruction.",
            order_index=0,
            difficulty_level="Intermediate",
            learning_objectives=[],
            estimated_duration_minutes=_module_duration_minutes(videos),
            rationale="Fallback grouping before curriculum reconstruction is complete.",
            confidence_score=0.0,
            video_count=len(videos),
            completed_count=completed_count,
            progress=progress,
            module_videos=entries,
        )

    def _build_health(
        self,
        *,
        space: LearningSpace,
        modules: list[LearningModuleRead],
        profiles: list[VideoCurriculumProfileRead],
        dependencies: list[VideoDependencyRead],
    ) -> CurriculumHealthRead:
        missing_transcript_count = sum(
            1
            for video in space.videos
            if not video.transcript_segments and video.transcript_status != COMPLETED
        )
        duplicate_topic_count = sum(1 for profile in profiles if profile.redundancy_signals)
        advanced_without_foundations_count = sum(
            1
            for profile in profiles
            if profile.difficulty_level == "Advanced"
            and not any(
                dependency.dependent_video_id == profile.video_id
                for dependency in dependencies
            )
        )
        manual_override_count = sum(1 for profile in profiles if profile.manual_override_locked)
        covered_video_ids = {
            entry.video_id
            for module in modules
            for entry in module.module_videos
        }
        unassigned_video_count = len(
            [video for video in space.videos if video.id not in covered_video_ids]
        )
        warnings: list[str] = []
        if missing_transcript_count:
            warnings.append(f"{missing_transcript_count} videos still lack transcript context.")
        if duplicate_topic_count:
            warnings.append("Some lessons still overlap heavily and may need review.")
        if advanced_without_foundations_count:
            warnings.append("Advanced lessons without explicit foundations were detected.")
        if unassigned_video_count:
            warnings.append("At least one video is not attached to a curriculum module.")

        score = max(
            0,
            100
            - (missing_transcript_count * 10)
            - (duplicate_topic_count * 4)
            - (advanced_without_foundations_count * 7)
            - (unassigned_video_count * 12),
        )
        latest_job = space.curriculum_jobs[0] if space.curriculum_jobs else None
        return CurriculumHealthRead(
            score=score,
            missing_transcript_count=missing_transcript_count,
            dependency_count=len(dependencies),
            duplicate_topic_count=duplicate_topic_count,
            advanced_without_foundations_count=advanced_without_foundations_count,
            manual_override_count=manual_override_count,
            unassigned_video_count=unassigned_video_count,
            warnings=warnings,
            generated_at=latest_job.finished_at if latest_job else None,
        )

    def _suggest_next_video(
        self,
        *,
        space: LearningSpace,
        modules: list[LearningModuleRead],
    ) -> SuggestedNextVideoRead | None:
        completed_ids = {video.id for video in space.videos if video.completed}
        dependency_map = defaultdict(set)
        for dependency in space.video_dependencies:
            dependency_map[dependency.dependent_video_id].add(dependency.prerequisite_video_id)

        for module in modules:
            for entry in module.module_videos:
                if entry.video.completed:
                    continue
                prerequisites = dependency_map.get(entry.video_id, set())
                if prerequisites and not prerequisites.issubset(completed_ids):
                    continue
                difficulty = (
                    entry.video.curriculum_profile.difficulty_level
                    if getattr(entry.video, "curriculum_profile", None)
                    else module.difficulty_level
                )
                return SuggestedNextVideoRead(
                    video_id=entry.video_id,
                    module_id=module.id,
                    title=entry.video.title,
                    module_title=module.title,
                    reason=(
                        "Next unlocked lesson based on prerequisites, module order, "
                        "and completion."
                    ),
                    difficulty_level=difficulty,
                )
        return None

    def _queue(self) -> Queue:
        redis = Redis.from_url(self.settings.redis_url)
        return Queue(self.settings.curriculum_queue_name, connection=redis)


def merge_payload(payload: dict[str, Any], **updates: Any) -> dict[str, Any]:
    return {**(payload or {}), **updates}


def clean_curriculum_error(error: Exception) -> str:
    if isinstance(error, ValueError):
        return str(error)
    return "Curriculum reconstruction failed. Try again."


def _module_duration_minutes(videos: list[Video]) -> int | None:
    total_seconds = sum(video.duration or 0 for video in videos)
    if total_seconds <= 0:
        return None
    return max(1, round(total_seconds / 60))


def _module_difficulty(profiles: list[VideoCurriculumProfile]) -> str:
    if not profiles:
        return "Intermediate"
    return max(profiles, key=_difficulty_weight).difficulty_level


def _module_objectives(profiles: list[VideoCurriculumProfile]) -> list[str]:
    objectives = []
    for profile in profiles:
        objectives.extend(profile.subtopics[:2] or profile.extracted_keywords[:2])
    return _dedupe_strings(objectives)[:5]


def _difficulty_weight(profile: VideoCurriculumProfile) -> int:
    return DIFFICULTY_ORDER.get(profile.difficulty_level, 1)


def _dedupe_strings(values: list[str]) -> list[str]:
    unique = []
    seen = set()
    for value in values:
        normalized = value.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(value.strip())
    return unique


def _profile_tokens(profile: VideoCurriculumProfile) -> set[str]:
    values = [profile.primary_topic, *profile.subtopics, *profile.extracted_keywords]
    return {_normalize_token(value) for value in values if _normalize_token(value)}


def _normalize_token(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _stable_topological_sort[T](
    *,
    nodes: list[T],
    edges: dict[T, set[T]],
    sort_key,
) -> list[T]:
    incoming = {node: set(edges.get(node, set())) for node in nodes}
    available = sorted([node for node in nodes if not incoming[node]], key=sort_key)
    result: list[T] = []

    while available:
        node = available.pop(0)
        result.append(node)
        for candidate in nodes:
            if node in incoming[candidate]:
                incoming[candidate].remove(node)
                if (
                    not incoming[candidate]
                    and candidate not in result
                    and candidate not in available
                ):
                    available.append(candidate)
        available.sort(key=sort_key)

    remaining = [node for node in nodes if node not in result]
    result.extend(sorted(remaining, key=sort_key))
    return result