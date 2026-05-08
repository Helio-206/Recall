from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings, get_settings
from app.schemas.curriculum import DifficultyLevel
from app.services.openrouter_provider import (
    OpenRouterAIError,
    _extract_error_detail,
    _extract_json_object,
    _extract_message_content,
    _get_openrouter_client,
    _get_rate_limiter,
)

if TYPE_CHECKING:
    from app.models.space import LearningSpace
    from app.models.video import Video

STOP_WORDS = {
    "about",
    "after",
    "also",
    "because",
    "been",
    "before",
    "being",
    "from",
    "into",
    "just",
    "lesson",
    "more",
    "over",
    "than",
    "that",
    "their",
    "there",
    "these",
    "this",
    "video",
    "what",
    "when",
    "with",
    "your",
}
DIFFICULTY_VALUES: tuple[DifficultyLevel, ...] = ("Beginner", "Intermediate", "Advanced")


@dataclass(slots=True)
class CurriculumVideoContext:
    video: Video
    original_position: int
    summary_text: str
    transcript_excerpt: str
    concept_names: list[str]
    note_text: str
    combined_text: str


@dataclass(slots=True)
class CurriculumProfileDraft:
    video_id: str
    primary_topic: str
    subtopics: list[str] = field(default_factory=list)
    difficulty_level: DifficultyLevel = "Beginner"
    prerequisite_topics: list[str] = field(default_factory=list)
    extracted_keywords: list[str] = field(default_factory=list)
    module_hint: str | None = None
    rationale: str | None = None
    confidence_score: float = 0.0
    estimated_sequence_score: float = 0.0


@dataclass(slots=True)
class CurriculumProviderResult:
    profiles: list[CurriculumProfileDraft]
    provider: str
    model: str
    request_count: int
    batch_count: int
    usage: dict[str, int] = field(default_factory=dict)


class CurriculumProvider(Protocol):
    def analyze_videos(
        self,
        *,
        space: LearningSpace,
        contexts: list[CurriculumVideoContext],
    ) -> CurriculumProviderResult: ...


class _CurriculumProfilePayload(BaseModel):
    video_id: str
    primary_topic: str
    subtopics: list[str] = Field(default_factory=list)
    difficulty_level: str = "Beginner"
    prerequisite_topics: list[str] = Field(default_factory=list)
    extracted_keywords: list[str] = Field(default_factory=list)
    module_hint: str | None = None
    rationale: str | None = None
    confidence_score: float = 0.0
    estimated_sequence_score: float = 0.0


class _CurriculumBatchPayload(BaseModel):
    profiles: list[_CurriculumProfilePayload] = Field(default_factory=list)


class HeuristicCurriculumProvider:
    def __init__(self, *, prompt_version: str) -> None:
        self.prompt_version = prompt_version

    def analyze_videos(
        self,
        *,
        space: LearningSpace,
        contexts: list[CurriculumVideoContext],
    ) -> CurriculumProviderResult:
        profiles = [self._build_profile(space=space, context=context) for context in contexts]
        return CurriculumProviderResult(
            profiles=profiles,
            provider="heuristic",
            model="heuristic",
            request_count=0,
            batch_count=1 if contexts else 0,
        )

    def _build_profile(
        self,
        *,
        space: LearningSpace,
        context: CurriculumVideoContext,
    ) -> CurriculumProfileDraft:
        keywords = _extract_keywords(context.combined_text, fallback=context.video.title)
        topic = _infer_primary_topic(context=context, keywords=keywords)
        difficulty = _infer_difficulty(video=context.video, text=context.combined_text)
        module_hint = _infer_module_hint(space=space, topic=topic, keywords=keywords)
        prerequisite_topics = _infer_prerequisite_topics(
            difficulty=difficulty,
            topic=topic,
            keywords=keywords,
        )
        return CurriculumProfileDraft(
            video_id=str(context.video.id),
            primary_topic=topic,
            subtopics=keywords[1:5],
            difficulty_level=difficulty,
            prerequisite_topics=prerequisite_topics,
            extracted_keywords=keywords[:6],
            module_hint=module_hint,
            rationale=(
                f"Clustered around {topic} based on transcript and summary keywords. "
                f"Estimated as {difficulty.lower()} from the lesson wording and depth."
            ),
            confidence_score=0.56,
            estimated_sequence_score=(
                _difficulty_rank(difficulty) + (context.original_position / 100)
            ),
        )


class OpenRouterCurriculumProvider:
    def __init__(self, *, settings: Settings, prompt_version: str) -> None:
        self.settings = settings
        self.prompt_version = prompt_version

    def analyze_videos(
        self,
        *,
        space: LearningSpace,
        contexts: list[CurriculumVideoContext],
    ) -> CurriculumProviderResult:
        if not self.settings.openrouter_api_key:
            raise OpenRouterAIError("OpenRouter is not configured. Set OPENROUTER_API_KEY.")

        profiles: list[CurriculumProfileDraft] = []
        request_count = 0
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        for batch in _chunk_list(contexts, self.settings.curriculum_batch_size):
            _get_rate_limiter(self.settings.ai_rate_limit_per_minute).wait()
            payload = _get_openrouter_client().post(
                "/chat/completions",
                json={
                    "model": self.settings.openrouter_model,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": _curriculum_system_prompt()},
                        {
                            "role": "user",
                            "content": _curriculum_user_prompt(
                                space=space,
                                contexts=batch,
                                prompt_version=self.prompt_version,
                            ),
                        },
                    ],
                },
                timeout=httpx.Timeout(self.settings.ai_request_timeout_seconds),
            )
            try:
                payload.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise OpenRouterAIError(_extract_error_detail(exc.response)) from exc

            body = payload.json()
            message = _extract_message_content(body)
            try:
                parsed = _CurriculumBatchPayload.model_validate(_extract_json_object(message))
            except ValidationError as exc:
                raise OpenRouterAIError("OpenRouter returned invalid curriculum JSON.") from exc

            profiles.extend(_normalize_batch_payload(parsed, contexts=batch))
            request_count += 1
            usage = _merge_usage(usage, body.get("usage") or {})

        return CurriculumProviderResult(
            profiles=profiles,
            provider="openrouter",
            model=self.settings.openrouter_model,
            request_count=request_count,
            batch_count=len(_chunk_list(contexts, self.settings.curriculum_batch_size)),
            usage=usage,
        )


class OllamaCurriculumProvider:
    def __init__(self, *, settings: Settings, prompt_version: str) -> None:
        self.settings = settings
        self.prompt_version = prompt_version

    def analyze_videos(
        self,
        *,
        space: LearningSpace,
        contexts: list[CurriculumVideoContext],
    ) -> CurriculumProviderResult:
        if not self.settings.ollama_model:
            raise ValueError("Ollama curriculum provider requires OLLAMA_MODEL.")

        client = httpx.Client(
            base_url=self.settings.ollama_base_url.rstrip("/"),
            timeout=httpx.Timeout(self.settings.ai_request_timeout_seconds),
        )
        profiles: list[CurriculumProfileDraft] = []
        request_count = 0

        for batch in _chunk_list(contexts, self.settings.curriculum_batch_size):
            response = client.post(
                "/api/generate",
                json={
                    "model": self.settings.ollama_model,
                    "format": "json",
                    "stream": False,
                    "prompt": _curriculum_system_prompt()
                    + "\n\n"
                    + _curriculum_user_prompt(
                        space=space,
                        contexts=batch,
                        prompt_version=self.prompt_version,
                    ),
                },
            )
            response.raise_for_status()
            body = response.json()
            try:
                parsed = _CurriculumBatchPayload.model_validate(
                    _extract_json_object(str(body.get("response") or "{}"))
                )
            except ValidationError as exc:
                raise ValueError("Ollama returned invalid curriculum JSON.") from exc

            profiles.extend(_normalize_batch_payload(parsed, contexts=batch))
            request_count += 1

        return CurriculumProviderResult(
            profiles=profiles,
            provider="ollama",
            model=self.settings.ollama_model,
            request_count=request_count,
            batch_count=len(_chunk_list(contexts, self.settings.curriculum_batch_size)),
        )


class ResilientCurriculumProvider:
    def __init__(self, primary: CurriculumProvider, fallback: CurriculumProvider) -> None:
        self.primary = primary
        self.fallback = fallback

    def analyze_videos(
        self,
        *,
        space: LearningSpace,
        contexts: list[CurriculumVideoContext],
    ) -> CurriculumProviderResult:
        try:
            return self.primary.analyze_videos(space=space, contexts=contexts)
        except Exception:
            return self.fallback.analyze_videos(space=space, contexts=contexts)


def get_curriculum_provider(*, prompt_version: str) -> CurriculumProvider:
    settings = get_settings()
    provider_name = resolve_curriculum_provider_name(settings)
    heuristic = HeuristicCurriculumProvider(prompt_version=prompt_version)

    if provider_name == "heuristic":
        return heuristic
    if provider_name == "openrouter":
        return ResilientCurriculumProvider(
            OpenRouterCurriculumProvider(settings=settings, prompt_version=prompt_version),
            heuristic,
        )
    if provider_name == "ollama":
        return ResilientCurriculumProvider(
            OllamaCurriculumProvider(settings=settings, prompt_version=prompt_version),
            heuristic,
        )
    return heuristic


def resolve_curriculum_provider_name(settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    provider_name = settings.curriculum_provider.strip().lower()
    if provider_name == "auto":
        if settings.openrouter_api_key:
            return "openrouter"
        if settings.ollama_model:
            return "ollama"
        return "heuristic"
    return provider_name


def build_video_contexts(videos: list[Video]) -> list[CurriculumVideoContext]:
    contexts: list[CurriculumVideoContext] = []
    for position, video in enumerate(sorted(videos, key=lambda item: item.order_index)):
        summary_parts = []
        if video.ai_summary:
            summary_parts = [
                part.strip()
                for part in [
                    video.ai_summary.short_summary,
                    video.ai_summary.detailed_summary,
                    video.ai_summary.learning_notes,
                ]
                if part and part.strip()
            ]
        transcript_excerpt = " ".join(
            segment.text.strip()
            for segment in video.transcript_segments[:10]
            if segment.text.strip()
        )
        concept_names = [concept.concept for concept in video.key_concepts[:6]]
        note_text = "\n".join(
            note.content.strip() for note in video.notes if getattr(note, "content", "").strip()
        )
        combined_text = "\n\n".join(
            part
            for part in [
                video.title,
                video.author or "",
                transcript_excerpt,
                "\n".join(summary_parts),
                ", ".join(concept_names),
                note_text,
            ]
            if part
        )
        contexts.append(
            CurriculumVideoContext(
                video=video,
                original_position=position,
                summary_text="\n".join(summary_parts),
                transcript_excerpt=transcript_excerpt,
                concept_names=concept_names,
                note_text=note_text,
                combined_text=combined_text,
            )
        )
    return contexts


def _curriculum_system_prompt() -> str:
    return (
        "You reorganize learning videos into a trustworthy curriculum graph. "
        "Return strict JSON with a top-level profiles array. Each profile must include: "
        "video_id, primary_topic, subtopics, difficulty_level, prerequisite_topics, "
        "extracted_keywords, module_hint, rationale, confidence_score, "
        "estimated_sequence_score. Difficulty must be Beginner, Intermediate, or Advanced."
    )


def _curriculum_user_prompt(
    *,
    space: LearningSpace,
    contexts: list[CurriculumVideoContext],
    prompt_version: str,
) -> str:
    serialized_contexts = [
        {
            "video_id": str(context.video.id),
            "title": context.video.title,
            "author": context.video.author,
            "duration_seconds": context.video.duration,
            "original_position": context.original_position,
            "summary": context.summary_text,
            "transcript_excerpt": context.transcript_excerpt,
            "concepts": context.concept_names,
        }
        for context in contexts
    ]
    return (
        f"Space title: {space.title}\n"
        f"Space topic: {space.topic or 'Unknown'}\n"
        f"Prompt version: {prompt_version}\n\n"
        "Analyze each lesson for topic, subtopics, difficulty, prerequisites, and the most "
        "sensible learning module. Preserve deterministic ordering logic and avoid random jumps. "
        "Return JSON only.\n\n"
        f"Videos:\n{json.dumps(serialized_contexts, ensure_ascii=True)}"
    )


def _normalize_batch_payload(
    payload: _CurriculumBatchPayload,
    *,
    contexts: list[CurriculumVideoContext],
) -> list[CurriculumProfileDraft]:
    context_by_id = {str(context.video.id): context for context in contexts}
    normalized: list[CurriculumProfileDraft] = []
    for item in payload.profiles:
        if item.video_id not in context_by_id:
            continue
        normalized.append(_normalize_profile_payload(item, context=context_by_id[item.video_id]))
    return normalized


def _normalize_profile_payload(
    payload: _CurriculumProfilePayload,
    *,
    context: CurriculumVideoContext,
) -> CurriculumProfileDraft:
    difficulty = _normalize_difficulty(payload.difficulty_level)
    extracted_keywords = _unique_strings(payload.extracted_keywords or [])
    if not extracted_keywords:
        extracted_keywords = _extract_keywords(context.combined_text, fallback=context.video.title)
    return CurriculumProfileDraft(
        video_id=str(context.video.id),
        primary_topic=_clean_text(payload.primary_topic, 180) or context.video.title,
        subtopics=_unique_strings(payload.subtopics or [], limit=6),
        difficulty_level=difficulty,
        prerequisite_topics=_unique_strings(payload.prerequisite_topics or [], limit=4),
        extracted_keywords=extracted_keywords[:6],
        module_hint=_clean_text(payload.module_hint or "", 180) or None,
        rationale=_clean_text(payload.rationale or "", 360) or None,
        confidence_score=max(0.0, min(float(payload.confidence_score or 0.0), 1.0)),
        estimated_sequence_score=max(float(payload.estimated_sequence_score or 0.0), 0.0),
    )


def _extract_keywords(text: str, *, fallback: str) -> list[str]:
    tokens = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", text)]
    filtered = [token for token in tokens if len(token) > 3 and token not in STOP_WORDS]
    if not filtered:
        filtered = [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9'-]+", fallback)]
    counts = Counter(filtered)
    return [token.replace("-", " ").title() for token, _ in counts.most_common(6)]


def _infer_primary_topic(
    *,
    context: CurriculumVideoContext,
    keywords: list[str],
) -> str:
    if context.concept_names:
        return context.concept_names[0]
    if keywords:
        return keywords[0]
    return context.video.title


def _infer_module_hint(
    *,
    space: LearningSpace,
    topic: str,
    keywords: list[str],
) -> str:
    normalized = {keyword.lower() for keyword in [topic, *keywords]}
    if normalized & {"linux", "bash", "terminal", "permissions", "filesystem"}:
        return "Linux Foundations"
    if normalized & {"docker", "containers", "kubernetes", "compose"}:
        return "Containers & Deployment"
    if normalized & {"python", "fastapi", "sqlalchemy", "backend"}:
        return "Python Backend"
    if normalized & {"react", "next", "typescript", "frontend", "tailwind"}:
        return "Web Frontend"
    if normalized & {"postgres", "database", "redis", "sql"}:
        return "Data Layer"
    if space.topic and space.topic.strip():
        return _clean_text(space.topic, 180)
    return _clean_text(topic, 180)


def _infer_difficulty(*, video: Video, text: str) -> DifficultyLevel:
    normalized = f"{video.title} {text}".lower()
    if any(term in normalized for term in ["advanced", "internals", "architecture", "hardening"]):
        return "Advanced"
    if any(term in normalized for term in ["beginner", "basics", "fundamentals", "intro", "101"]):
        return "Beginner"
    if (video.duration or 0) <= 600:
        return "Beginner"
    if any(term in normalized for term in ["deep dive", "optimization", "performance"]):
        return "Advanced"
    return "Intermediate"


def _infer_prerequisite_topics(
    *,
    difficulty: DifficultyLevel,
    topic: str,
    keywords: list[str],
) -> list[str]:
    if difficulty == "Beginner":
        return []
    seeds = [topic, *keywords]
    prerequisites = []
    if difficulty == "Intermediate":
        prerequisites = seeds[:2]
    if difficulty == "Advanced":
        prerequisites = seeds[:3]
    return [item for item in _unique_strings(prerequisites, limit=3) if item != topic]


def _difficulty_rank(value: DifficultyLevel) -> int:
    return {"Beginner": 0, "Intermediate": 1, "Advanced": 2}[value]


def _normalize_difficulty(value: str | None) -> DifficultyLevel:
    normalized = (value or "").strip().lower()
    if normalized.startswith("adv"):
        return "Advanced"
    if normalized.startswith("beg") or normalized.startswith("introduction"):
        return "Beginner"
    return "Intermediate"


def _clean_text(value: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _unique_strings(values: list[str], *, limit: int = 6) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean_text(value, 80)
        normalized = cleaned.lower()
        if not cleaned or normalized in seen:
            continue
        seen.add(normalized)
        unique.append(cleaned)
        if len(unique) == limit:
            break
    return unique


def _chunk_list[T](values: list[T], size: int) -> list[list[T]]:
    if not values:
        return []
    safe_size = max(size, 1)
    return [values[index : index + safe_size] for index in range(0, len(values), safe_size)]


def _merge_usage(current: dict[str, int], update: dict[str, Any]) -> dict[str, int]:
    return {
        "prompt_tokens": int(current.get("prompt_tokens", 0)) + int(update.get("prompt_tokens", 0)),
        "completion_tokens": int(current.get("completion_tokens", 0))
        + int(update.get("completion_tokens", 0)),
        "total_tokens": int(current.get("total_tokens", 0)) + int(update.get("total_tokens", 0)),
    }