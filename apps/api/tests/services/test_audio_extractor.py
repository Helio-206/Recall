from pathlib import Path
from types import ModuleType, SimpleNamespace

from app.services.audio_extractor import TemporaryAudioExtractor


def test_extracts_compact_mp3_audio(monkeypatch, tmp_path: Path) -> None:
    captured_options: dict[str, object] = {}

    class FakeYoutubeDL:
        def __init__(self, options: dict[str, object]) -> None:
            captured_options.update(options)

        def __enter__(self) -> "FakeYoutubeDL":
            return self

        def __exit__(self, exc_type, exc, tb) -> bool:
            return False

        def extract_info(self, video_url: str, download: bool = True) -> dict[str, object]:
            assert video_url == "https://example.com/watch?v=123"
            assert download is True
            (tmp_path / "source.mp3").write_bytes(b"ID3")
            return {"id": "123"}

    fake_yt_dlp = ModuleType("yt_dlp")
    fake_yt_dlp.YoutubeDL = FakeYoutubeDL

    fake_utils = ModuleType("yt_dlp.utils")
    fake_utils.DownloadError = RuntimeError
    fake_utils.ExtractorError = RuntimeError

    monkeypatch.setattr(
        "app.services.audio_extractor.resolve_ffmpeg_path",
        lambda: "/usr/bin/ffmpeg",
    )
    monkeypatch.setattr(
        "app.services.audio_extractor.get_settings",
        lambda: SimpleNamespace(yt_dlp_socket_timeout_seconds=20),
    )
    monkeypatch.setitem(__import__("sys").modules, "yt_dlp", fake_yt_dlp)
    monkeypatch.setitem(__import__("sys").modules, "yt_dlp.utils", fake_utils)

    audio_path = TemporaryAudioExtractor().extract(
        video_url="https://example.com/watch?v=123",
        output_dir=tmp_path,
    )

    assert audio_path == tmp_path / "source.mp3"
    assert captured_options["ffmpeg_location"] == "/usr/bin/ffmpeg"
    assert captured_options["postprocessor_args"] == ["-ac", "1", "-ar", "16000", "-b:a", "48k"]
    assert captured_options["postprocessors"] == [
        {
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "48",
        }
    ]
