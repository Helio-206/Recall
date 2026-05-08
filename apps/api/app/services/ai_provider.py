from __future__ import annotations

import re
from collections import Counter
from typing import Protocol

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.transcript_segment import TranscriptSegment
from app.models.video import Video
from app.services.ai_chunking import TranscriptChunk

STOP_WORDS = {
    "about",
    "after",
    "also",
    "because",
    "been",
    "being",
    "between",
    "could",
    "every",
    "from",
    "have",
    "into",
    "just",
    "more",
    "most",
    "other",
    "some",
    "than",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "video",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "would",
    "your",
}


class KeyConceptDraft(BaseModel):
    concept: str
    relevance_score: float = Field(ge=0.0, le=1.0)


class ReviewQuestionDraft(BaseModel):
    question: str
    answer: str


class ImportantMomentDraft(BaseModel):
    title: str
    timestamp: float = Field(ge=0.0)
    description: str


class LearningInsightsDraft(BaseModel):
    short_summary: str
    detailed_summary: str
    learning_notes: str
    key_concepts: list[KeyConceptDraft]
    key_takeaways: list[str]
    review_questions: list[ReviewQuestionDraft]
    important_moments: list[ImportantMomentDraft]


class LearningProviderResult(BaseModel):
    draft: LearningInsightsDraft
    provider: str
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
    request_count: int = 0
    chunk_count: int = 0
    fallback_model: str | None = None
    models_tried: list[str] = Field(default_factory=list)


class AILearningProvider(Protocol):
    def generate(
        self,
        *,
        video: Video,
        chunks: list[TranscriptChunk],
        segments: list[TranscriptSegment],
    ) -> LearningProviderResult: ...


class HeuristicLearningProvider:
    def __init__(self, *, prompt_version: str) -> None:
        self.prompt_version = prompt_version

    def generate(
        self,
        *,
        video: Video,
        chunks: list[TranscriptChunk],
        segments: list[TranscriptSegment],
    ) -> LearningProviderResult:
        chunk_summaries = [
            self._summarize_chunk(chunk.text) for chunk in chunks if chunk.text.strip()
        ]
        detailed_summary = "\n\n".join(chunk_summaries[:5]) or self._fallback_summary(segments)
        short_summary = self._truncate(
            chunk_summaries[0] if chunk_summaries else detailed_summary,
            280,
        )

        concepts = self._extract_key_concepts(video=video, segments=segments)
        takeaways = self._build_takeaways(chunk_summaries, segments)
        questions = self._build_review_questions(video=video, concepts=concepts, segments=segments)
        moments = self._build_important_moments(segments)
        notes = self._build_learning_notes(video=video, takeaways=takeaways, concepts=concepts)

        return LearningProviderResult(
            draft=LearningInsightsDraft(
                short_summary=short_summary,
                detailed_summary=detailed_summary,
                learning_notes=notes,
                key_concepts=concepts,
                key_takeaways=takeaways,
                review_questions=questions,
                important_moments=moments,
            ),
            provider="heuristic",
            model="heuristic",
            chunk_count=len(chunks),
            request_count=0,
        )

    def _summarize_chunk(self, text: str) -> str:
        sentences = _split_sentences(text)
        if not sentences:
            return self._truncate(text.strip(), 360)
        selected = " ".join(sentences[:2])
        return self._truncate(selected, 420)

    def _fallback_summary(self, segments: list[TranscriptSegment]) -> str:
        combined = " ".join(segment.text.strip() for segment in segments[:12])
        return self._truncate(combined, 420)

    def _extract_key_concepts(
        self,
        *,
        video: Video,
        segments: list[TranscriptSegment],
    ) -> list[KeyConceptDraft]:
        tokens = re.findall(
            r"[A-Za-z][A-Za-z0-9'-]+",
            f"{video.title} " + " ".join(segment.text for segment in segments),
        )
        filtered = [
            token.lower()
            for token in tokens
            if len(token) > 3 and token.lower() not in STOP_WORDS
        ]
        if not filtered:
            return [KeyConceptDraft(concept=video.title, relevance_score=1.0)]

        counts = Counter(filtered)
        max_count = max(counts.values())
        concepts: list[KeyConceptDraft] = []
        for concept, count in counts.most_common(6):
            concepts.append(
                KeyConceptDraft(
                    concept=concept.replace("-", " ").title(),
                    relevance_score=round(count / max_count, 2),
                )
            )
        return concepts

    def _build_takeaways(
        self,
        chunk_summaries: list[str],
        segments: list[TranscriptSegment],
    ) -> list[str]:
        candidates = [summary for summary in chunk_summaries if len(summary) > 40]
        if not candidates:
            candidates = [
                segment.text.strip() for segment in segments if len(segment.text.strip()) > 50
            ]

        unique: list[str] = []
        for candidate in candidates:
            normalized = candidate.strip()
            if normalized and normalized not in unique:
                unique.append(self._truncate(normalized, 220))
            if len(unique) == 5:
                break
        return unique

    def _build_review_questions(
        self,
        *,
        video: Video,
        concepts: list[KeyConceptDraft],
        segments: list[TranscriptSegment],
    ) -> list[ReviewQuestionDraft]:
        questions: list[ReviewQuestionDraft] = []
        for concept in concepts[:4]:
            supporting = self._find_supporting_sentence(concept.concept, segments)
            questions.append(
                ReviewQuestionDraft(
                    question=f"How does {concept.concept} shape the main lesson in {video.title}?",
                    answer=(
                        supporting
                        or f"{concept.concept} appears repeatedly as a central idea in this lesson."
                    ),
                )
            )
        return questions

    def _build_important_moments(
        self,
        segments: list[TranscriptSegment],
    ) -> list[ImportantMomentDraft]:
        if not segments:
            return []

        candidates = [segment for segment in segments if len(segment.text.strip()) >= 45]
        if not candidates:
            candidates = segments

        step = max(1, len(candidates) // 4)
        selected: list[ImportantMomentDraft] = []
        last_timestamp = -999.0
        for index in range(0, len(candidates), step):
            segment = candidates[index]
            if segment.start_time - last_timestamp < 45:
                continue
            title = self._truncate(" ".join(segment.text.strip().split()[:8]), 72)
            selected.append(
                ImportantMomentDraft(
                    title=title.rstrip(".,;:"),
                    timestamp=segment.start_time,
                    description=self._truncate(segment.text.strip(), 180),
                )
            )
            last_timestamp = segment.start_time
            if len(selected) == 5:
                break
        return selected

    def _build_learning_notes(
        self,
        *,
        video: Video,
        takeaways: list[str],
        concepts: list[KeyConceptDraft],
    ) -> str:
        concept_line = ", ".join(concept.concept for concept in concepts[:4]) or video.title
        takeaway_lines = "\n".join(f"- {item}" for item in takeaways[:4])
        return (
            f"Focus concepts: {concept_line}.\n\nStudy notes:\n{takeaway_lines}".strip()
        )

    def _find_supporting_sentence(
        self,
        concept: str,
        segments: list[TranscriptSegment],
    ) -> str | None:
        concept_lower = concept.lower()
        for segment in segments:
            text = segment.text.strip()
            if concept_lower in text.lower():
                return self._truncate(text, 220)
        return None

    def _truncate(self, text: str, limit: int) -> str:
        normalized = re.sub(r"\s+", " ", text).strip()
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 1].rstrip() + "..."


def get_ai_learning_provider(*, prompt_version: str) -> AILearningProvider:
    settings = get_settings()
    provider_name = settings.ai_provider.strip().lower()

    if provider_name == "auto":
        provider_name = "openrouter" if settings.openrouter_api_key else "heuristic"

    if provider_name == "heuristic":
        return HeuristicLearningProvider(prompt_version=prompt_version)

    if provider_name == "openrouter":
        from app.services.openrouter_provider import OpenRouterLearningProvider

        return OpenRouterLearningProvider(prompt_version=prompt_version)

    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")


def _split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", normalized)
        if sentence.strip()
    ]