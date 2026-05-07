from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

from app.core.config import get_settings
from app.core.statuses import SourceType


class MetadataExtractionError(Exception):
    """Raised when source metadata cannot be extracted safely."""


@dataclass(frozen=True)
class ExtractedVideo:
    title: str
    url: str
    thumbnail: str | None
    author: str | None
    duration: int | None
    source_order: int


@dataclass(frozen=True)
class ExtractedSource:
    source_type: SourceType
    title: str | None
    author: str | None
    thumbnail: str | None
    duration: int | None
    videos: list[ExtractedVideo]
    skipped_count: int


class MetadataExtractor:
    youtube_hosts = {
        "youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtube-nocookie.com",
        "youtu.be",
    }

    def validate_youtube_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"} or host not in self.youtube_hosts:
            raise MetadataExtractionError("Paste a valid YouTube video or playlist URL.")
        return url

    def detect_source_type(self, url: str) -> SourceType:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.strip("/")
        query = parse_qs(parsed.query)

        if "list" in query or path.startswith("playlist"):
            return "playlist"
        if path.startswith("@") or path.startswith("channel/") or path.startswith("c/"):
            return "channel"
        if (
            host == "youtu.be"
            or "v" in query
            or path.startswith("shorts/")
            or path.startswith("embed/")
        ):
            return "single_video"
        raise MetadataExtractionError("Paste a valid YouTube video or playlist URL.")

    def extract(self, url: str) -> ExtractedSource:
        source_type = self.detect_source_type(url)
        if source_type == "channel":
            raise MetadataExtractionError("Channel ingestion is not available yet.")

        try:
            from yt_dlp import YoutubeDL
            from yt_dlp.utils import DownloadError, ExtractorError
        except ImportError as exc:
            raise MetadataExtractionError("Metadata extraction is not available.") from exc

        settings = get_settings()
        ydl_options = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "ignoreerrors": True,
            "extract_flat": "in_playlist" if source_type == "playlist" else False,
            "noplaylist": source_type == "single_video",
            "playlistend": settings.ingestion_max_playlist_items,
            "socket_timeout": settings.yt_dlp_socket_timeout_seconds,
            "retries": 2,
            "fragment_retries": 0,
        }

        try:
            with YoutubeDL(ydl_options) as ydl:
                raw_info = ydl.extract_info(url, download=False)
        except (DownloadError, ExtractorError) as exc:
            raise MetadataExtractionError("We could not read that YouTube source.") from exc
        except Exception as exc:
            raise MetadataExtractionError("Metadata extraction failed.") from exc

        if not raw_info:
            raise MetadataExtractionError("No available videos were found for that source.")

        if source_type == "playlist" or raw_info.get("_type") == "playlist":
            return self._extract_playlist(raw_info)
        return self._extract_single(raw_info)

    def _extract_single(self, raw_info: dict) -> ExtractedSource:
        video = self._normalize_video(raw_info, source_order=0)
        if not video:
            raise MetadataExtractionError("No available video metadata was found.")
        return ExtractedSource(
            source_type="single_video",
            title=raw_info.get("title"),
            author=raw_info.get("uploader") or raw_info.get("channel"),
            thumbnail=self._thumbnail(raw_info),
            duration=self._duration(raw_info),
            videos=[video],
            skipped_count=0,
        )

    def _extract_playlist(self, raw_info: dict) -> ExtractedSource:
        videos: list[ExtractedVideo] = []
        skipped_count = 0
        entries = raw_info.get("entries") or []
        for entry in entries:
            if not entry:
                skipped_count += 1
                continue
            video = self._normalize_video(entry, source_order=len(videos))
            if video:
                videos.append(video)
            else:
                skipped_count += 1

        if not videos:
            raise MetadataExtractionError("No available playlist videos were found.")

        return ExtractedSource(
            source_type="playlist",
            title=raw_info.get("title"),
            author=raw_info.get("uploader") or raw_info.get("channel"),
            thumbnail=self._thumbnail(raw_info) or videos[0].thumbnail,
            duration=sum(video.duration or 0 for video in videos) or None,
            videos=videos,
            skipped_count=skipped_count,
        )

    def _normalize_video(self, entry: dict, *, source_order: int) -> ExtractedVideo | None:
        video_id = self._video_id(entry)
        url = self._canonical_video_url(entry, video_id)
        title = entry.get("title") or entry.get("fulltitle")
        if not url or not title:
            return None
        return ExtractedVideo(
            title=title[:220],
            url=url,
            thumbnail=self._thumbnail(entry),
            author=entry.get("uploader") or entry.get("channel") or entry.get("creator"),
            duration=self._duration(entry),
            source_order=source_order,
        )

    @staticmethod
    def _duration(entry: dict) -> int | None:
        duration = entry.get("duration")
        if duration is None:
            return None
        try:
            return int(duration)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _thumbnail(entry: dict) -> str | None:
        thumbnail = entry.get("thumbnail")
        if thumbnail:
            return thumbnail
        thumbnails = entry.get("thumbnails") or []
        for candidate in reversed(thumbnails):
            url = candidate.get("url") if isinstance(candidate, dict) else None
            if url:
                return url
        return None

    @staticmethod
    def _video_id(entry: dict) -> str | None:
        candidate = entry.get("id")
        if isinstance(candidate, str) and candidate:
            return candidate
        for key in ("webpage_url", "original_url", "url"):
            value = entry.get(key)
            if not isinstance(value, str):
                continue
            parsed = urlparse(value)
            if parsed.netloc.lower().removeprefix("www.") == "youtu.be":
                return parsed.path.strip("/") or None
            query_id = parse_qs(parsed.query).get("v", [None])[0]
            if query_id:
                return query_id
        return None

    @staticmethod
    def _canonical_video_url(entry: dict, video_id: str | None) -> str | None:
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        for key in ("webpage_url", "original_url", "url"):
            value = entry.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value
        return None
