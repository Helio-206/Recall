import os
from functools import lru_cache
from importlib.util import find_spec
from pathlib import Path
from shutil import copy2

from app.core.config import get_settings
from app.repositories.transcript_segments import TranscriptSegmentDraft
from app.services.audio_extractor import resolve_ffmpeg_path


class TranscriptionError(Exception):
    """Raised when Whisper cannot produce usable transcript segments."""


class WhisperTranscriber:
    def transcribe(self, audio_path: Path) -> list[TranscriptSegmentDraft]:
        if find_spec("whisper") is None:
            raise TranscriptionError("Whisper is not installed in the transcript worker.")

        settings = get_settings()
        try:
            _ensure_ffmpeg_on_path()
            model = _get_whisper_model(settings.whisper_model_name)
            options = {
                "fp16": settings.whisper_fp16,
                "task": "transcribe",
                "verbose": None,
            }
            if settings.whisper_language:
                options["language"] = settings.whisper_language
            result = model.transcribe(str(audio_path), **options)
        except Exception as exc:
            raise TranscriptionError("Whisper transcription failed.") from exc

        segments: list[TranscriptSegmentDraft] = []
        for segment in result.get("segments") or []:
            text = str(segment.get("text") or "").strip()
            if not text:
                continue
            start_time = _coerce_timestamp(segment.get("start"))
            end_time = _coerce_timestamp(segment.get("end"))
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

        if not segments:
            text = str(result.get("text") or "").strip()
            if text:
                segments.append(
                    TranscriptSegmentDraft(
                        start_time=0,
                        end_time=0.25,
                        text=text,
                        order_index=0,
                    )
                )

        if not segments:
            raise TranscriptionError("Whisper did not return transcript text.")
        return segments


def _coerce_timestamp(value: object) -> float:
    try:
        return max(float(value), 0)
    except (TypeError, ValueError):
        return 0


def _ensure_ffmpeg_on_path() -> None:
    ffmpeg_path = resolve_ffmpeg_path()
    if not ffmpeg_path:
        raise TranscriptionError("FFmpeg is not available for Whisper.")

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


@lru_cache(maxsize=2)
def _get_whisper_model(model_name: str):
    import whisper

    return whisper.load_model(model_name)
