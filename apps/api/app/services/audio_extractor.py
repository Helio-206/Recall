from pathlib import Path
from shutil import which

from app.core.config import get_settings


class AudioExtractionError(Exception):
    """Raised when temporary audio cannot be extracted for transcription."""


class TemporaryAudioExtractor:
    def extract(self, *, video_url: str, output_dir: Path) -> Path:
        ffmpeg_location = resolve_ffmpeg_path()
        if ffmpeg_location is None:
            raise AudioExtractionError("FFmpeg is not installed in the transcript worker.")

        try:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError, ExtractorError
        except ImportError as exc:
            raise AudioExtractionError("Audio extraction is not available.") from exc

        output_dir.mkdir(parents=True, exist_ok=True)
        settings = get_settings()
        ydl_options = {
            "format": "bestaudio/best",
            "outtmpl": str(output_dir / "source.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
            "skip_download": False,
            "socket_timeout": settings.yt_dlp_socket_timeout_seconds,
            "retries": 2,
            "fragment_retries": 2,
            "ffmpeg_location": ffmpeg_location,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "wav",
                    "preferredquality": "64",
                }
            ],
        }

        try:
            with YoutubeDL(ydl_options) as ydl:
                ydl.extract_info(video_url, download=True)
        except (DownloadError, ExtractorError) as exc:
            raise AudioExtractionError("We could not prepare audio for this video.") from exc
        except Exception as exc:
            raise AudioExtractionError("Audio preparation failed.") from exc

        wav_files = sorted(output_dir.glob("*.wav"))
        if not wav_files:
            raise AudioExtractionError("FFmpeg did not produce a transcript-ready audio file.")
        return wav_files[0]


def resolve_ffmpeg_path() -> str | None:
    system_ffmpeg = which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
    except ImportError:
        return None

    return imageio_ffmpeg.get_ffmpeg_exe()
