from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from app.core.config import get_settings
from app.repositories.transcript_segments import TranscriptSegmentDraft


class CaptionExtractionError(Exception):
    """Raised when YouTube captions exist but cannot be parsed."""


@dataclass(slots=True)
class CaptionTranscript:
    segments: list[TranscriptSegmentDraft]
    language: str
    source: str


@dataclass(slots=True)
class _CaptionCandidate:
    url: str
    extension: str
    language: str
    source: str


class YouTubeCaptionExtractor:
    def extract(self, *, video_url: str) -> CaptionTranscript | None:
        try:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError, ExtractorError
        except ImportError as exc:
            raise CaptionExtractionError("Caption extraction is not available.") from exc

        settings = get_settings()
        ydl_options = {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "socket_timeout": settings.yt_dlp_socket_timeout_seconds,
        }

        try:
            with YoutubeDL(ydl_options) as ydl:
                info = ydl.extract_info(video_url, download=False)
        except (DownloadError, ExtractorError):
            return None
        except Exception as exc:
            raise CaptionExtractionError("We could not read captions for this video.") from exc

        candidate = self._select_candidate(info or {})
        if not candidate:
            return None

        raw_text = self._download_caption(candidate.url)
        if candidate.extension == "json3":
            raw_segments = _parse_json3(raw_text)
        else:
            raw_segments = _parse_vtt(raw_text)

        segments = _merge_segments(raw_segments)
        if not segments:
            return None

        return CaptionTranscript(
            segments=segments,
            language=candidate.language,
            source=candidate.source,
        )

    def _select_candidate(self, info: dict[str, Any]) -> _CaptionCandidate | None:
        settings = get_settings()
        language_priority = [
            language
            for language in (
                settings.whisper_language,
                "en",
                "pt",
                "pt-BR",
                "pt-PT",
            )
            if language
        ]

        subtitles = info.get("subtitles") or {}
        automatic_captions = info.get("automatic_captions") or {}
        return _pick_caption(subtitles, language_priority, "youtube_captions") or _pick_caption(
            automatic_captions,
            language_priority,
            "youtube_auto_captions",
        )

    def _download_caption(self, url: str) -> str:
        settings = get_settings()
        request = Request(url, headers={"User-Agent": "Recall/0.1"})
        try:
            with urlopen(request, timeout=settings.yt_dlp_socket_timeout_seconds) as response:
                return response.read().decode("utf-8", errors="replace")
        except (OSError, URLError) as exc:
            raise CaptionExtractionError("We could not download captions for this video.") from exc


def _pick_caption(
    caption_map: dict[str, list[dict[str, Any]]],
    language_priority: list[str],
    source: str,
) -> _CaptionCandidate | None:
    if not caption_map:
        return None

    languages = [language for language in language_priority if language in caption_map]
    languages.extend(language for language in caption_map if language not in languages)

    for language in languages:
        formats = caption_map.get(language) or []
        for extension in ("json3", "vtt"):
            for item in formats:
                item_extension = str(item.get("ext") or "").lower()
                item_url = item.get("url")
                if item_extension == extension and item_url:
                    return _CaptionCandidate(
                        url=str(item_url),
                        extension=extension,
                        language=language,
                        source=source,
                    )
    return None


def _parse_json3(raw_text: str) -> list[TranscriptSegmentDraft]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CaptionExtractionError("YouTube captions were not valid JSON.") from exc

    segments: list[TranscriptSegmentDraft] = []
    for event in payload.get("events") or []:
        text = "".join(str(seg.get("utf8") or "") for seg in event.get("segs") or [])
        text = _clean_text(text)
        if not text:
            continue

        start_time = max(float(event.get("tStartMs") or 0) / 1000, 0)
        duration = max(float(event.get("dDurationMs") or 3000) / 1000, 0.25)
        segments.append(
            TranscriptSegmentDraft(
                start_time=start_time,
                end_time=start_time + duration,
                text=text,
                order_index=len(segments),
            )
        )
    return segments


def _parse_vtt(raw_text: str) -> list[TranscriptSegmentDraft]:
    segments: list[TranscriptSegmentDraft] = []
    blocks = re.split(r"\n\s*\n", raw_text.replace("\r\n", "\n"))
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0].upper().startswith(("WEBVTT", "NOTE")):
            continue

        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), -1)
        if timing_index < 0:
            continue

        start_raw, end_raw = lines[timing_index].split("-->", 1)
        start_time = _parse_vtt_timestamp(start_raw.strip())
        end_time = _parse_vtt_timestamp(end_raw.split()[0].strip())
        text = _clean_text(" ".join(lines[timing_index + 1 :]))
        if not text:
            continue
        if end_time <= start_time:
            end_time = start_time + 0.25

        segments.append(
            TranscriptSegmentDraft(
                start_time=start_time,
                end_time=end_time,
                text=text,
                order_index=len(segments),
            )
        )
    return segments


def _parse_vtt_timestamp(value: str) -> float:
    parts = value.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        return float(value)
    except ValueError:
        return 0


def _merge_segments(
    segments: list[TranscriptSegmentDraft],
    *,
    max_chars: int = 360,
    max_duration: float = 18,
    max_gap: float = 1.5,
) -> list[TranscriptSegmentDraft]:
    if not segments:
        return []

    merged: list[TranscriptSegmentDraft] = []
    current_start = segments[0].start_time
    current_end = segments[0].end_time
    current_text = segments[0].text

    for segment in segments[1:]:
        gap = segment.start_time - current_end
        next_duration = segment.end_time - current_start
        next_text = f"{current_text} {segment.text}".strip()
        should_merge = (
            gap <= max_gap
            and next_duration <= max_duration
            and len(next_text) <= max_chars
            and not current_text.endswith((".", "?", "!"))
        )
        if should_merge:
            current_end = max(current_end, segment.end_time)
            current_text = next_text
            continue

        merged.append(
            TranscriptSegmentDraft(
                start_time=current_start,
                end_time=max(current_end, current_start + 0.25),
                text=current_text,
                order_index=len(merged),
            )
        )
        current_start = segment.start_time
        current_end = segment.end_time
        current_text = segment.text

    merged.append(
        TranscriptSegmentDraft(
            start_time=current_start,
            end_time=max(current_end, current_start + 0.25),
            text=current_text,
            order_index=len(merged),
        )
    )
    return merged


def _clean_text(value: str) -> str:
    text = html.unescape(value)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text.replace("\n", " "))
    return text.strip()
