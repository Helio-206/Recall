from __future__ import annotations

import json
import logging
import re
import time
from collections import deque
from functools import lru_cache
from threading import Lock
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.models.transcript_segment import TranscriptSegment
from app.models.video import Video
from app.services.ai_chunking import TranscriptChunk
from app.services.ai_provider import (
    ImportantMomentDraft,
    KeyConceptDraft,
    LearningInsightsDraft,
    LearningProviderResult,
    ReviewQuestionDraft,
)

logger = logging.getLogger(__name__)


class OpenRouterAIError(ValueError):
    """Raised when the OpenRouter provider cannot produce a valid response."""


class _ChunkSummaryDraft(BaseModel):
    summary: str


class OpenRouterLearningProvider:
    def __init__(self, *, prompt_version: str) -> None:
        self.prompt_version = prompt_version
        self.settings = get_settings()

    def generate(
        self,
        *,
        video: Video,
        chunks: list[TranscriptChunk],
        segments: list[TranscriptSegment],
    ) -> LearningProviderResult:
        if not self.settings.openrouter_api_key:
            raise OpenRouterAIError("OpenRouter is not configured. Set OPENROUTER_API_KEY.")

        effective_chunks = [chunk for chunk in chunks if chunk.text.strip()]
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        models_tried: list[str] = []
        request_count = 0
        fallback_model: str | None = None

        if len(effective_chunks) <= 1:
            source_material = (
                effective_chunks[0].text if effective_chunks else _segments_excerpt(segments)
            )
        else:
            chunk_summaries: list[str] = []
            for chunk in effective_chunks:
                chunk_result, metadata = self._request_structured(
                    system_prompt=_chunk_system_prompt(),
                    user_prompt=_chunk_user_prompt(video=video, chunk=chunk),
                    schema=_ChunkSummaryDraft,
                )
                chunk_summaries.append(
                    f"Chunk {chunk.order_index + 1} "
                    f"({_format_timestamp(chunk.start_time)}"
                    f" - {_format_timestamp(chunk.end_time)}): "
                    f"{chunk_result.summary.strip()}"
                )
                usage = _merge_usage(usage, metadata["usage"])
                models_tried.extend(metadata["models_tried"])
                request_count += 1
                if metadata["fallback_model"]:
                    fallback_model = metadata["fallback_model"]

            source_material = "\n".join(chunk_summaries)

        draft, metadata = self._request_structured(
            system_prompt=_insights_system_prompt(),
            user_prompt=_insights_user_prompt(video=video, transcript_material=source_material),
            schema=LearningInsightsDraft,
        )
        usage = _merge_usage(usage, metadata["usage"])
        models_tried.extend(metadata["models_tried"])
        request_count += 1
        if metadata["fallback_model"]:
            fallback_model = metadata["fallback_model"]

        normalized = _normalize_learning_draft(draft=draft, video=video, segments=segments)
        return LearningProviderResult(
            draft=normalized,
            provider="openrouter",
            model=metadata["model"],
            usage=usage,
            request_count=request_count,
            chunk_count=len(effective_chunks),
            fallback_model=fallback_model,
            models_tried=_dedupe(models_tried),
        )

    def _request_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, Any]]:
        models = [self.settings.openrouter_model, *self.settings.openrouter_fallback_model_list]
        last_error: Exception | None = None

        for model_index, model in enumerate(models):
            for attempt in range(self.settings.ai_request_retries + 1):
                _get_rate_limiter(self.settings.ai_rate_limit_per_minute).wait()
                try:
                    payload = _get_openrouter_client().post(
                        "/chat/completions",
                        json={
                            "model": model,
                            "temperature": 0.2,
                            "response_format": {"type": "json_object"},
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                        },
                    )
                    payload.raise_for_status()
                    body = payload.json()
                    content = _extract_message_content(body)
                    parsed_payload = _prepare_payload_for_schema(
                        schema=schema,
                        payload=_extract_json_object(content),
                    )
                    parsed = schema.model_validate(parsed_payload)
                    return parsed, {
                        "model": model,
                        "usage": _extract_usage(body),
                        "models_tried": models[: model_index + 1],
                        "fallback_model": model if model_index > 0 else None,
                    }
                except ValidationError as exc:
                    last_error = OpenRouterAIError("OpenRouter returned invalid structured output.")
                    logger.warning(
                        "OpenRouter structured output validation failed for model %s: %s",
                        model,
                        exc,
                    )
                except httpx.TimeoutException:
                    last_error = OpenRouterAIError("OpenRouter request timed out.")
                except httpx.HTTPStatusError as exc:
                    status_code = exc.response.status_code
                    detail = _extract_error_detail(exc.response)
                    if status_code in {400, 401, 403}:
                        raise OpenRouterAIError(detail) from exc
                    last_error = OpenRouterAIError(detail)
                except (httpx.HTTPError, OpenRouterAIError, json.JSONDecodeError) as exc:
                    last_error = OpenRouterAIError(str(exc) or "OpenRouter request failed.")

                if attempt < self.settings.ai_request_retries:
                    time.sleep(min(2 ** attempt, 4))

        if last_error:
            raise last_error
        raise OpenRouterAIError("OpenRouter request failed.")


class _SlidingWindowRateLimiter:
    def __init__(self, max_calls: int, period_seconds: float = 60.0) -> None:
        self.max_calls = max_calls
        self.period_seconds = period_seconds
        self.calls: deque[float] = deque()
        self.lock = Lock()

    def wait(self) -> None:
        if self.max_calls <= 0:
            return

        while True:
            with self.lock:
                now = time.monotonic()
                while self.calls and now - self.calls[0] >= self.period_seconds:
                    self.calls.popleft()
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return
                sleep_for = self.period_seconds - (now - self.calls[0])
            time.sleep(max(sleep_for, 0.05))


@lru_cache(maxsize=1)
def _get_openrouter_client() -> httpx.Client:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "X-Title": settings.openrouter_app_name,
    }
    if settings.openrouter_site_url:
        headers["HTTP-Referer"] = settings.openrouter_site_url

    return httpx.Client(
        base_url=settings.openrouter_base_url.rstrip("/"),
        timeout=httpx.Timeout(settings.ai_request_timeout_seconds),
        headers=headers,
    )


@lru_cache(maxsize=8)
def _get_rate_limiter(max_calls: int) -> _SlidingWindowRateLimiter:
    return _SlidingWindowRateLimiter(max_calls=max_calls)


def _chunk_system_prompt() -> str:
    return (
        "You summarize transcript chunks for a learning platform. "
        "Return strict JSON with a single field named summary."
    )


def _chunk_user_prompt(*, video: Video, chunk: TranscriptChunk) -> str:
    return (
        f"Video title: {video.title}\n"
        f"Chunk window: {_format_timestamp(chunk.start_time)}"
        f" - {_format_timestamp(chunk.end_time)}\n\n"
        "Summarize the teaching content in 2-4 sentences. "
        "Focus on what is actually explained, "
        "not generic filler. Return JSON only.\n\n"
        f"Transcript chunk:\n{chunk.text}"
    )


def _insights_system_prompt() -> str:
    return (
        "You are an educational AI that creates structured learning summaries. "
        "Return strict JSON with these fields: short_summary, detailed_summary, "
        "learning_notes, key_concepts (array of {concept, relevance_score}), "
        "key_takeaways (array of strings), review_questions (array of {question, answer}), "
        "important_moments (array of {title, timestamp, description})."
    )


def _insights_user_prompt(*, video: Video, transcript_material: str) -> str:
    return (
        f"Video title: {video.title}\n"
        f"Author: {video.author or 'Unknown'}\n"
        f"Prompt version: {get_settings().ai_prompt_version}\n\n"
        "Generate:\n"
        "- a short summary under 280 characters\n"
        "- a detailed summary\n"
        "- learning notes that feel like study notes\n"
        "- 4 to 6 key concepts with relevance_score from 0 to 1\n"
        "- 3 to 5 key takeaways\n"
        "- 3 to 5 review questions with answers\n"
        "- up to 5 important moments with timestamps in seconds\n\n"
        "Return JSON only.\n\n"
        f"Transcript material:\n{transcript_material}"
    )


def _extract_message_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices") or []
    if not choices:
        raise OpenRouterAIError("OpenRouter returned no choices.")

    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(item.get("text") or "") for item in content if isinstance(item, dict)
        ).strip()
    raise OpenRouterAIError("OpenRouter returned an unsupported message payload.")


def _extract_json_object(text: str) -> dict[str, Any]:
    normalized = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", normalized, flags=re.DOTALL)
    if fenced:
        normalized = fenced.group(1)
    else:
        start = normalized.find("{")
        end = normalized.rfind("}")
        if start >= 0 and end > start:
            normalized = normalized[start : end + 1]

    parsed = json.loads(normalized)
    if not isinstance(parsed, dict):
        raise OpenRouterAIError("OpenRouter did not return a JSON object.")
    return parsed


def _prepare_payload_for_schema(
    *,
    schema: type[BaseModel],
    payload: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(payload)

    if schema is LearningInsightsDraft:
        for field_name in ("short_summary", "detailed_summary", "learning_notes"):
            value = normalized.get(field_name)
            if isinstance(value, list):
                normalized[field_name] = "\n".join(
                    str(item).strip() for item in value if str(item).strip()
                )

        takeaways = normalized.get("key_takeaways")
        if isinstance(takeaways, str):
            normalized["key_takeaways"] = [takeaways]

        questions = normalized.get("review_questions")
        if isinstance(questions, dict):
            normalized["review_questions"] = [questions]

        moments = normalized.get("important_moments")
        if isinstance(moments, dict):
            normalized["important_moments"] = [moments]

        concepts = normalized.get("key_concepts")
        if isinstance(concepts, dict):
            normalized["key_concepts"] = [concepts]

    if schema is _ChunkSummaryDraft:
        summary = normalized.get("summary")
        if isinstance(summary, list):
            normalized["summary"] = " ".join(
                str(item).strip() for item in summary if str(item).strip()
            )

    return normalized


def _extract_usage(payload: dict[str, Any]) -> dict[str, int]:
    usage = payload.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"OpenRouter request failed with status {response.status_code}."

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            if isinstance(message, str) and message.strip():
                return message
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip():
            return detail
    return f"OpenRouter request failed with status {response.status_code}."


def _merge_usage(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {
        "prompt_tokens": left.get("prompt_tokens", 0) + right.get("prompt_tokens", 0),
        "completion_tokens": left.get("completion_tokens", 0) + right.get("completion_tokens", 0),
        "total_tokens": left.get("total_tokens", 0) + right.get("total_tokens", 0),
    }


def _segments_excerpt(segments: list[TranscriptSegment], limit: int = 12) -> str:
    return " ".join(segment.text.strip() for segment in segments[:limit] if segment.text.strip())


def _normalize_learning_draft(
    *,
    draft: LearningInsightsDraft,
    video: Video,
    segments: list[TranscriptSegment],
) -> LearningInsightsDraft:
    fallback_summary = _truncate(_segments_excerpt(segments) or video.title, 280)
    max_timestamp = max((segment.end_time for segment in segments), default=0.0)

    seen_concepts: set[str] = set()
    key_concepts: list[KeyConceptDraft] = []
    for item in draft.key_concepts:
        concept = _clean_text(item.concept, 220)
        normalized_key = concept.lower()
        if not concept or normalized_key in seen_concepts:
            continue
        seen_concepts.add(normalized_key)
        key_concepts.append(
            KeyConceptDraft(
                concept=concept,
                relevance_score=max(0.0, min(item.relevance_score, 1.0)),
            )
        )
        if len(key_concepts) == 6:
            break

    takeaways = _unique_strings(draft.key_takeaways, limit=5, max_length=220)

    review_questions: list[ReviewQuestionDraft] = []
    for item in draft.review_questions:
        question = _clean_text(item.question, 220)
        answer = _clean_text(item.answer, 320)
        if question and answer:
            review_questions.append(ReviewQuestionDraft(question=question, answer=answer))
        if len(review_questions) == 5:
            break

    important_moments: list[ImportantMomentDraft] = []
    for item in draft.important_moments:
        title = _clean_text(item.title, 120)
        description = _clean_text(item.description, 220)
        timestamp = max(0.0, min(item.timestamp, max_timestamp))
        if title and description:
            important_moments.append(
                ImportantMomentDraft(title=title, timestamp=timestamp, description=description)
            )
        if len(important_moments) == 5:
            break

    return LearningInsightsDraft(
        short_summary=_clean_text(draft.short_summary, 280) or fallback_summary,
        detailed_summary=_clean_text(draft.detailed_summary, 4_000) or fallback_summary,
        learning_notes=_clean_text(draft.learning_notes, 4_000) or fallback_summary,
        key_concepts=key_concepts,
        key_takeaways=takeaways or [fallback_summary],
        review_questions=review_questions,
        important_moments=important_moments,
    )


def _unique_strings(values: list[str], *, limit: int, max_length: int) -> list[str]:
    unique: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = _clean_text(value, max_length)
        if not cleaned or cleaned.lower() in seen:
            continue
        seen.add(cleaned.lower())
        unique.append(cleaned)
        if len(unique) == limit:
            break
    return unique


def _clean_text(value: str, limit: int) -> str:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _format_timestamp(value: float) -> str:
    total_seconds = max(int(value), 0)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def _truncate(value: str, limit: int) -> str:
    return _clean_text(value, limit)


def _dedupe(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique