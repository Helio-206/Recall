from __future__ import annotations

from dataclasses import dataclass

from app.models.transcript_segment import TranscriptSegment


@dataclass(frozen=True)
class TranscriptChunk:
    order_index: int
    start_time: float
    end_time: float
    text: str
    segment_count: int


def chunk_transcript_segments(
    segments: list[TranscriptSegment],
    *,
    target_chars: int,
    overlap_segments: int,
) -> list[TranscriptChunk]:
    if not segments:
        return []

    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = []
    current_chars = 0

    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue

        if current and current_chars >= target_chars:
            chunks.append(_to_chunk(current, len(chunks)))
            current = current[-overlap_segments:] if overlap_segments > 0 else []
            current_chars = sum(len(item.text.strip()) for item in current)

        current.append(segment)
        current_chars += len(text)

    if current:
        chunks.append(_to_chunk(current, len(chunks)))

    return chunks


def _to_chunk(segments: list[TranscriptSegment], order_index: int) -> TranscriptChunk:
    text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
    return TranscriptChunk(
        order_index=order_index,
        start_time=segments[0].start_time,
        end_time=segments[-1].end_time,
        text=text,
        segment_count=len(segments),
    )