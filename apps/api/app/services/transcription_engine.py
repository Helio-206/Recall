import os
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory
from typing import Any, Protocol

import httpx

from app.core.config import get_settings
from app.repositories.transcript_segments import TranscriptSegmentDraft
from app.services.audio_extractor import resolve_ffmpeg_path


class TranscriptionError(Exception):
    """Raised when a transcription provider cannot produce usable segments."""


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> list[TranscriptSegmentDraft]: ...


class WhisperTranscriber:
    def transcribe(self, audio_path: Path) -> list[TranscriptSegmentDraft]:
        if find_spec("faster_whisper") is None:
            raise TranscriptionError("faster-whisper is not installed in the transcript worker.")

        settings = get_settings()
        try:
            _ensure_ffmpeg_on_path()
            model = _get_whisper_model(settings.whisper_model_name, settings.whisper_fp16)
            options = {
                "task": "transcribe",
                "temperature": 0.0,
                "beam_size": 1,
                "best_of": 1,
                "condition_on_previous_text": False,
                "vad_filter": True,
            }
            if settings.whisper_language:
                options["language"] = settings.whisper_language
            result, _ = model.transcribe(str(audio_path), **options)
            decoded_segments = list(result)
        except Exception as exc:
            raise TranscriptionError("Local Whisper transcription failed.") from exc

        segments = _drafts_from_values(
            (segment.start, segment.end, str(segment.text or "")) for segment in decoded_segments
        )
        if not segments:
            raise TranscriptionError("Local Whisper did not return transcript text.")
        return segments


class GroqTranscriber:
    endpoint = "https://api.groq.com/openai/v1/audio/transcriptions"

    def transcribe(self, audio_path: Path) -> list[TranscriptSegmentDraft]:
        settings = get_settings()
        if not settings.groq_api_key:
            raise TranscriptionError("Groq transcription is not configured.")

        try:
            with _groq_audio_chunks(audio_path) as audio_chunks:
                drafts: list[TranscriptSegmentDraft] = []
                for chunk_path, offset_seconds in audio_chunks:
                    drafts.extend(self._transcribe_chunk(chunk_path, offset_seconds))
        except TranscriptionError:
            raise
        except (OSError, subprocess.SubprocessError, httpx.HTTPError) as exc:
            raise TranscriptionError("Groq transcription failed. Try again.") from exc

        if not drafts:
            raise TranscriptionError("Groq did not return transcript text.")
        return _reindex(drafts)

    def _transcribe_chunk(
        self,
        audio_path: Path,
        offset_seconds: float,
    ) -> list[TranscriptSegmentDraft]:
        settings = get_settings()
        data = {
            "model": settings.groq_transcription_model,
            "response_format": "verbose_json",
            "temperature": "0",
            "timestamp_granularities[]": "segment",
        }
        if settings.whisper_language:
            data["language"] = settings.whisper_language

        with audio_path.open("rb") as audio_file:
            response = httpx.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                data=data,
                files={"file": (audio_path.name, audio_file, _mime_type(audio_path))},
                timeout=settings.groq_timeout_seconds,
            )
        if response.status_code >= 400:
            raise TranscriptionError("Groq could not transcribe this audio.")

        try:
            payload = response.json()
        except ValueError as exc:
            raise TranscriptionError("Groq returned an invalid transcription response.") from exc

        segments = _drafts_from_groq_payload(payload, offset_seconds)
        if segments:
            return segments

        text = str(payload.get("text") or "").strip() if isinstance(payload, dict) else ""
        if not text:
            return []
        return [
            TranscriptSegmentDraft(
                start_time=offset_seconds,
                end_time=offset_seconds + 0.25,
                text=text,
                order_index=0,
            )
        ]


def get_transcriber() -> tuple[str, Transcriber]:
    settings = get_settings()
    provider = settings.transcript_provider.strip().lower()
    if provider == "groq" or (provider == "auto" and settings.groq_api_key):
        return "groq", GroqTranscriber()
    if provider in {"auto", "faster-whisper", "local"}:
        return "faster-whisper", WhisperTranscriber()
    raise TranscriptionError("Transcript provider is not supported.")


def configured_transcription_model() -> str:
    settings = get_settings()
    provider = settings.transcript_provider.strip().lower()
    if provider == "groq" or (provider == "auto" and settings.groq_api_key):
        return settings.groq_transcription_model
    return settings.whisper_model_name


@contextmanager
def _groq_audio_chunks(audio_path: Path) -> Generator[list[tuple[Path, float]], None, None]:
    settings = get_settings()
    if audio_path.stat().st_size <= settings.groq_max_upload_bytes:
        yield [(audio_path, 0.0)]
        return

    ffmpeg_path = resolve_ffmpeg_path()
    if not ffmpeg_path:
        raise TranscriptionError("FFmpeg is not available to split audio for Groq.")

    with TemporaryDirectory(prefix="recall-groq-audio-", dir=audio_path.parent) as temp_dir:
        output_pattern = Path(temp_dir) / "chunk-%03d.mp3"
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(audio_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "48k",
            "-f",
            "segment",
            "-segment_time",
            str(settings.groq_chunk_duration_seconds),
            "-reset_timestamps",
            "1",
            str(output_pattern),
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        chunks = sorted(Path(temp_dir).glob("chunk-*.mp3"))
        if not chunks:
            raise TranscriptionError("Audio could not be split for Groq.")

        prepared_chunks: list[tuple[Path, float]] = []
        for index, chunk in enumerate(chunks):
            prepared_chunks.append((chunk, index * settings.groq_chunk_duration_seconds))
        yield prepared_chunks


def _drafts_from_groq_payload(payload: Any, offset_seconds: float) -> list[TranscriptSegmentDraft]:
    if not isinstance(payload, dict):
        return []
    raw_segments = payload.get("segments") or []
    if not isinstance(raw_segments, list):
        return []
    return _drafts_from_values(
        (
            _coerce_timestamp(segment.get("start")) + offset_seconds,
            _coerce_timestamp(segment.get("end")) + offset_seconds,
            str(segment.get("text") or ""),
        )
        for segment in raw_segments
        if isinstance(segment, dict)
    )


def _drafts_from_values(
    values: Any,
) -> list[TranscriptSegmentDraft]:
    segments: list[TranscriptSegmentDraft] = []
    for start, end, raw_text in values:
        text = raw_text.strip()
        if not text:
            continue
        start_time = _coerce_timestamp(start)
        end_time = _coerce_timestamp(end)
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


def _reindex(segments: list[TranscriptSegmentDraft]) -> list[TranscriptSegmentDraft]:
    return [
        TranscriptSegmentDraft(
            start_time=segment.start_time,
            end_time=segment.end_time,
            text=segment.text,
            order_index=index,
        )
        for index, segment in enumerate(segments)
    ]


def _mime_type(path: Path) -> str:
    return {
        ".m4a": "audio/mp4",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }.get(path.suffix.lower(), "application/octet-stream")


def _coerce_timestamp(value: object) -> float:
    try:
        return max(float(value), 0)
    except (TypeError, ValueError):
        return 0


def _ensure_ffmpeg_on_path() -> None:
    ffmpeg_path = resolve_ffmpeg_path()
    if not ffmpeg_path:
        raise TranscriptionError("FFmpeg is not available for transcription.")

    ffmpeg_dir = str(_path_directory_with_ffmpeg_alias(Path(ffmpeg_path)))
    current_path = os.environ.get("PATH", "")
    if ffmpeg_dir not in current_path.split(os.pathsep):
        os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{current_path}"


def _path_directory_with_ffmpeg_alias(ffmpeg_path: Path) -> Path:
    if ffmpeg_path.name == "ffmpeg":
        return ffmpeg_path.parent

    alias_dir = Path("/tmp/recall-ffmpeg-bin")
    alias_dir.mkdir(parents=True, exist_ok=True)
    alias_path = alias_dir / "ffmpeg"
    if alias_path.exists():
        return alias_dir

    try:
        alias_path.symlink_to(ffmpeg_path)
    except OSError:
        copy2(ffmpeg_path, alias_path)
        alias_path.chmod(0o755)

    return alias_dir


@lru_cache(maxsize=4)
def _get_whisper_model(model_name: str, use_fp16: bool):
    from faster_whisper import WhisperModel

    if use_fp16:
        try:
            return WhisperModel(model_name, device="auto", compute_type="float16")
        except Exception:
            pass
    return WhisperModel(model_name, device="auto", compute_type="int8")
