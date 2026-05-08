from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.extension_save_event import ExtensionSaveEvent
from app.repositories.extension_save_events import ExtensionSaveEventRepository
from app.repositories.spaces import LearningSpaceRepository
from app.schemas.extension import (
    ExtensionRecentSaveRead,
    ExtensionSaveAccepted,
    ExtensionSaveRequest,
    ExtensionSpaceRead,
)
from app.schemas.ingestion import IngestionRequest
from app.services.ingestion_service import IngestionService
from app.services.spaces import LearningSpaceService


@dataclass(frozen=True)
class CaptureTarget:
    url: str
    normalized_url: str
    platform: str
    source_type: str
    is_supported: bool
    reason: str | None = None


class BrowserExtensionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.events = ExtensionSaveEventRepository(db)
        self.ingestion = IngestionService(db)
        self.spaces = LearningSpaceRepository(db)

    def list_spaces(self, *, user_id: UUID) -> list[ExtensionSpaceRead]:
        spaces = LearningSpaceService(self.db).list_for_user(user_id)
        return [
            ExtensionSpaceRead(
                id=space.id,
                title=space.title,
                topic=space.topic,
                progress=space.progress,
                video_count=space.video_count,
                updated_at=space.updated_at,
            )
            for space in spaces
        ]

    def list_recent_saves(self, *, user_id: UUID) -> list[ExtensionRecentSaveRead]:
        return [
            self._serialize_recent_save(event)
            for event in self.events.list_recent_for_user(
                user_id=user_id,
                limit=self.settings.extension_recent_saves_limit,
            )
        ]

    def save_url(
        self,
        *,
        user_id: UUID,
        payload: ExtensionSaveRequest,
    ) -> ExtensionSaveAccepted:
        space = self.spaces.get_for_user(space_id=payload.space_id, user_id=user_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Learning space not found.",
            )

        target = classify_capture_url(str(payload.url))
        event = self.events.create(
            user_id=user_id,
            space_id=space.id,
            url=str(payload.url),
            normalized_url=target.normalized_url,
            platform=target.platform,
            source_type=target.source_type,
            status="pending",
            page_title=payload.page_title,
            page_description=payload.page_description,
            browser=payload.browser,
            extension_version=payload.extension_version,
            page_metadata={
                "submitted_from": "browser_extension",
                "page_title": payload.page_title,
                "page_description": payload.page_description,
            },
        )

        self._enforce_rate_limit(user_id=user_id, event=event)

        if not target.is_supported:
            self.events.update_status(event, status="unsupported", error_message=target.reason)
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=target.reason or "This page is not supported yet.",
            )

        try:
            accepted = self.ingestion.ingest(
                space_id=space.id,
                user_id=user_id,
                payload=IngestionRequest(
                    url=target.normalized_url,
                    title=payload.page_title,
                ),
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Save failed."
            self.events.update_status(event, status="failed", error_message=detail)
            self.db.commit()
            raise

        self.events.update_status(
            event,
            status="accepted",
            error_message=None,
            source_id=accepted.source_id,
            ingestion_job_id=accepted.job_id,
        )
        self.db.commit()

        return ExtensionSaveAccepted(
            save_id=event.id,
            job_id=accepted.job_id,
            source_id=accepted.source_id,
            status=accepted.status,
            platform=target.platform,
            source_type=target.source_type,
            normalized_url=target.normalized_url,
            message="Added to Learning Space.",
        )

    def _enforce_rate_limit(
        self,
        *,
        user_id: UUID,
        event: ExtensionSaveEvent,
    ) -> None:
        created_after = datetime.now(UTC) - timedelta(
            minutes=self.settings.extension_save_rate_limit_window_minutes
        )
        recent_attempts = self.events.count_for_user_since(
            user_id=user_id,
            created_after=created_after,
        )
        if recent_attempts <= self.settings.extension_save_rate_limit_count:
            return

        message = "Too many save attempts. Please wait a moment and try again."
        self.events.update_status(event, status="rate_limited", error_message=message)
        self.db.commit()
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=message)

    @staticmethod
    def _serialize_recent_save(event: ExtensionSaveEvent) -> ExtensionRecentSaveRead:
        live_status = event.status
        error_message = event.error_message
        if event.ingestion_job:
            live_status = event.ingestion_job.status
            error_message = event.ingestion_job.error_message or error_message
        elif event.source:
            live_status = event.source.status
            error_message = event.source.error_message or error_message

        return ExtensionRecentSaveRead(
            id=event.id,
            space_id=event.space_id,
            space_title=event.space.title,
            source_id=event.source_id,
            job_id=event.ingestion_job_id,
            url=event.url,
            normalized_url=event.normalized_url,
            platform=event.platform,
            source_type=event.source_type,
            status=live_status,
            error_message=error_message,
            page_title=event.page_title,
            created_at=event.created_at,
            open_path=f"/spaces/{event.space_id}",
        )


def classify_capture_url(url: str) -> CaptureTarget:
    parsed = urlparse(url)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.strip("/")
    query = parse_qs(parsed.query)

    if parsed.scheme not in {"http", "https"}:
        return CaptureTarget(
            url=url,
            normalized_url=url,
            platform="web",
            source_type="page",
            is_supported=False,
            reason="Only public http(s) pages are supported.",
        )

    if host in {
        "youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtube-nocookie.com",
        "youtu.be",
    }:
        source_type = _detect_youtube_source_type(host=host, path=path, query=query)
        return CaptureTarget(
            url=url,
            normalized_url=_normalize_youtube_url(
                url,
                host=host,
                path=path,
                query=query,
                source_type=source_type,
            ),
            platform="youtube",
            source_type=source_type,
            is_supported=True,
        )

    if host in {"x.com", "twitter.com", "mobile.twitter.com"}:
        return _unsupported_target(url=url, platform="x", source_type="post")
    if host.endswith("tiktok.com"):
        return _unsupported_target(url=url, platform="tiktok", source_type="short_video")
    if host.endswith("instagram.com"):
        return _unsupported_target(url=url, platform="instagram", source_type="reel")
    if host == "vimeo.com" or host.endswith("vimeo.com"):
        return _unsupported_target(url=url, platform="vimeo", source_type="video")

    return _unsupported_target(url=url, platform="web", source_type="page")


def _detect_youtube_source_type(
    *,
    host: str,
    path: str,
    query: dict[str, list[str]],
) -> str:
    if "list" in query or path.startswith("playlist"):
        return "playlist"
    if (
        path.startswith("@")
        or path.startswith("channel/")
        or path.startswith("c/")
        or path.startswith("user/")
    ):
        return "channel"
    if (
        host == "youtu.be"
        or "v" in query
        or path.startswith("shorts/")
        or path.startswith("embed/")
    ):
        return "single_video"
    return "single_video"


def _normalize_youtube_url(
    url: str,
    *,
    host: str,
    path: str,
    query: dict[str, list[str]],
    source_type: str,
) -> str:
    if source_type == "playlist" and query.get("list"):
        return f"https://www.youtube.com/playlist?{urlencode({'list': query['list'][0]})}"
    if source_type == "channel":
        normalized_path = f"/{path}" if path else urlparse(url).path or "/"
        return urlunparse(("https", "www.youtube.com", normalized_path, "", "", ""))
    if host == "youtu.be":
        video_id = path.split("/", 1)[0]
        return f"https://www.youtube.com/watch?{urlencode({'v': video_id})}"
    video_id = query.get("v", [None])[0]
    if video_id:
        return f"https://www.youtube.com/watch?{urlencode({'v': video_id})}"
    if path.startswith("shorts/") or path.startswith("embed/"):
        video_id = path.split("/", 1)[1].split("/", 1)[0]
        return f"https://www.youtube.com/watch?{urlencode({'v': video_id})}"
    return url


def _unsupported_target(*, url: str, platform: str, source_type: str) -> CaptureTarget:
    return CaptureTarget(
        url=url,
        normalized_url=url,
        platform=platform,
        source_type=source_type,
        is_supported=False,
        reason="This page is not supported yet.",
    )