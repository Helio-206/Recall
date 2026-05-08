from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

LOCAL_CORS_ORIGIN_REGEX = (
    r"^https?://"
    r"(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})"
    r"(:\d+)?$"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Recall API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://recall:recall@localhost:5433/recall"
    redis_url: str = "redis://localhost:6379/0"

    ingestion_queue_name: str = "recall-ingestion"
    ingestion_job_timeout_seconds: int = 900
    ingestion_retry_attempts: int = 2
    ingestion_max_playlist_items: int = 100
    yt_dlp_socket_timeout_seconds: int = 20
    transcript_queue_name: str = "recall-transcripts"
    transcript_job_timeout_seconds: int = 7200
    transcript_retry_attempts: int = 1
    transcript_tmp_path: Path = Path("/tmp/recall-transcripts")
    transcript_prefer_youtube_captions: bool = True
    whisper_model_name: str = "tiny"
    whisper_language: str | None = None
    whisper_fp16: bool = False

    jwt_secret_key: str = Field(default="change-me-before-production", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7

    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    backend_cors_origin_regex: str | None = None
    browser_extension_cors_origin_regex: str | None = r"^chrome-extension://[a-p]{32}$"
    local_storage_path: Path = Path("./storage")

    ai_provider: str = "heuristic"
    ai_prompt_version: str = "phase4-v1"
    ai_queue_name: str = "ai-summary"
    ai_retry_attempts: int = 2
    ai_job_timeout_seconds: int = 60 * 8
    ai_chunk_target_chars: int = 1800
    ai_chunk_overlap_segments: int = 1
    ai_request_timeout_seconds: float = 45.0
    ai_request_retries: int = 2
    ai_rate_limit_per_minute: int = 20
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "openai/gpt-oss-120b:free"
    openrouter_fallback_models: str = ""
    openrouter_app_name: str = "Recall"
    openrouter_site_url: str | None = None
    curriculum_provider: str = "heuristic"
    curriculum_prompt_version: str = "phase6-v1"
    curriculum_queue_name: str = "curriculum-reconstruction"
    curriculum_retry_attempts: int = 1
    curriculum_job_timeout_seconds: int = 60 * 10
    curriculum_batch_size: int = 6
    extension_save_rate_limit_count: int = 15
    extension_save_rate_limit_window_minutes: int = 5
    extension_recent_saves_limit: int = 8
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str | None = None

    search_enabled: bool = True
    search_backend: str = "meilisearch"
    search_url: str = "http://localhost:7700"
    search_api_key: str | None = None
    search_index_uid: str = "learning-content"
    search_timeout_seconds: int = 5
    search_task_wait_seconds: float = 5.0
    search_excerpt_words: int = 24

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        patterns = [pattern for pattern in [self.backend_cors_origin_regex] if pattern]
        if self.environment == "local":
            patterns.append(LOCAL_CORS_ORIGIN_REGEX)
        if self.browser_extension_cors_origin_regex:
            patterns.append(self.browser_extension_cors_origin_regex)
        return "|".join(patterns) if patterns else None

    @property
    def openrouter_fallback_model_list(self) -> list[str]:
        return [
            model.strip()
            for model in self.openrouter_fallback_models.split(",")
            if model.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
