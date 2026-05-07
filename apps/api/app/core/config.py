from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LOCAL_CORS_ORIGIN_REGEX = (
    r"^https?://"
    r"(localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})"
    r"(:\d+)?$"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Recall API"
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://recall:recall@localhost:5432/recall"
    redis_url: str = "redis://localhost:6379/0"
    ingestion_queue_name: str = "recall-ingestion"
    ingestion_job_timeout_seconds: int = 900
    ingestion_retry_attempts: int = 2
    ingestion_max_playlist_items: int = 100
    yt_dlp_socket_timeout_seconds: int = 20

    jwt_secret_key: str = Field(default="change-me-before-production", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7

    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    backend_cors_origin_regex: str | None = None
    local_storage_path: Path = Path("./storage")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.backend_cors_origin_regex:
            return self.backend_cors_origin_regex
        if self.environment == "local":
            return LOCAL_CORS_ORIGIN_REGEX
        return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
