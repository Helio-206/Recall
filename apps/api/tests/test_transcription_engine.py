from pathlib import Path
from types import SimpleNamespace

from app.services import transcription_engine


class _GroqResponse:
    status_code = 200

    @staticmethod
    def json() -> dict[str, object]:
        return {
            "text": "First sentence. Second sentence.",
            "segments": [
                {"start": 0.5, "end": 2.0, "text": " First sentence. "},
                {"start": 2.0, "end": 4.5, "text": "Second sentence."},
            ],
        }


def test_groq_transcriber_preserves_segment_timestamps(monkeypatch, tmp_path: Path) -> None:
    audio_path = tmp_path / "source.mp3"
    audio_path.write_bytes(b"audio")
    captured: dict[str, object] = {}
    settings = SimpleNamespace(
        groq_api_key="test-key",
        groq_transcription_model="whisper-large-v3-turbo",
        groq_timeout_seconds=10,
        groq_max_upload_bytes=1024,
        groq_chunk_duration_seconds=60,
        whisper_language="pt",
    )

    def fake_post(*args: object, **kwargs: object) -> _GroqResponse:
        captured.update(kwargs)
        return _GroqResponse()

    monkeypatch.setattr(transcription_engine, "get_settings", lambda: settings)
    monkeypatch.setattr(transcription_engine.httpx, "post", fake_post)

    segments = transcription_engine.GroqTranscriber().transcribe(audio_path)

    assert [(segment.start_time, segment.end_time, segment.text) for segment in segments] == [
        (0.5, 2.0, "First sentence."),
        (2.0, 4.5, "Second sentence."),
    ]
    assert captured["data"] == [
        ("model", "whisper-large-v3-turbo"),
        ("response_format", "verbose_json"),
        ("temperature", "0"),
        ("timestamp_granularities[]", "segment"),
        ("language", "pt"),
    ]


def test_auto_provider_uses_groq_only_when_a_key_exists(monkeypatch) -> None:
    monkeypatch.setattr(
        transcription_engine,
        "get_settings",
        lambda: SimpleNamespace(
            transcript_provider="auto",
            groq_api_key="test-key",
            groq_transcription_model="whisper-large-v3-turbo",
            whisper_model_name="tiny",
        ),
    )

    provider, transcriber = transcription_engine.get_transcriber()

    assert provider == "groq"
    assert isinstance(transcriber, transcription_engine.GroqTranscriber)
    assert transcription_engine.configured_transcription_model() == "whisper-large-v3-turbo"
