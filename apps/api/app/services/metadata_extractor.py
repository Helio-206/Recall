from dataclasses import dataclass
import re
from urllib.parse import parse_qs, urlparse

import httpx

from app.core.config import get_settings
from app.core.statuses import Platform, SourceType


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

    coursera_hosts = {
        "coursera.org",
        "www.coursera.org",
    }

    def validate_source_url(self, url: str) -> str:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if parsed.scheme not in {"http", "https"}:
            raise MetadataExtractionError("Paste a valid source URL (YouTube or Coursera).")
        if host not in self.youtube_hosts and host not in {"coursera.org"}:
            raise MetadataExtractionError(
                "Paste a valid YouTube or Coursera URL."
            )
        return url

    def detect_platform(self, url: str) -> Platform:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        if host in self.youtube_hosts:
            return "youtube"
        if host in {"coursera.org"}:
            return "coursera"
        raise MetadataExtractionError("Paste a valid YouTube or Coursera URL.")

    def detect_source_type(self, url: str) -> SourceType:
        platform = self.detect_platform(url)
        if platform == "coursera":
            return "single_video"

        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.")
        path = parsed.path.strip("/")
        query = parse_qs(parsed.query)

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
        raise MetadataExtractionError("Paste a valid YouTube video, playlist, or channel URL.")

    def extract(self, url: str) -> ExtractedSource:
        platform = self.detect_platform(url)
        if platform == "coursera":
            return self._extract_coursera(url)

        source_type = self.detect_source_type(url)

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
            "extract_flat": "in_playlist" if source_type in {"playlist", "channel"} else False,
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

        if source_type in {"playlist", "channel"} or raw_info.get("_type") == "playlist":
            return self._extract_collection(raw_info, source_type=source_type)
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

    def _extract_collection(self, raw_info: dict, *, source_type: SourceType) -> ExtractedSource:
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
            collection_label = "channel" if source_type == "channel" else "playlist"
            raise MetadataExtractionError(f"No available {collection_label} videos were found.")

        return ExtractedSource(
            source_type=source_type,
            title=raw_info.get("title"),
            author=raw_info.get("uploader") or raw_info.get("channel"),
            thumbnail=self._thumbnail(raw_info) or videos[0].thumbnail,
            duration=sum(video.duration or 0 for video in videos) or None,
            videos=videos,
            skipped_count=skipped_count,
        )

    def _extract_coursera(self, url: str) -> ExtractedSource:
        title = self._coursera_title_from_url(url)
        author = "Coursera"
        thumbnail = None

        try:
            response = httpx.get(
                url,
                timeout=10.0,
                follow_redirects=True,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/126.0.0.0 Safari/537.36"
                    )
                },
            )
            if response.status_code < 400:
                html = response.text[:350000]
                title = self._match_meta_content(html, "og:title") or title
                thumbnail = self._match_meta_content(html, "og:image")
                author = self._match_meta_content(html, "og:site_name") or author
        except Exception:
            pass

        video = ExtractedVideo(
            title=title[:220],
            url=url,
            thumbnail=thumbnail,
            author=author,
            duration=None,
            source_order=0,
        )
        return ExtractedSource(
            source_type="single_video",
            title=title,
            author=author,
            thumbnail=thumbnail,
            duration=None,
            videos=[video],
            skipped_count=0,
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

    @staticmethod
    def _coursera_title_from_url(url: str) -> str:
        parsed = urlparse(url)
        parts = [part for part in parsed.path.split("/") if part]
        if not parts:
            return "Coursera lesson"
        slug = parts[-1].replace("-", " ").replace("_", " ").strip()
        slug = re.sub(r"\s+", " ", slug)
        return slug.title() if slug else "Coursera lesson"

    @staticmethod
    def _match_meta_content(html: str, property_name: str) -> str | None:
        pattern = re.compile(
            rf'<meta[^>]+property=["\']{re.escape(property_name)}["\'][^>]+content=["\']([^"\']+)["\']',
            re.IGNORECASE,
        )
        match = pattern.search(html)
        if match:
            return match.group(1).strip()

        fallback_pattern = re.compile(
            rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']{re.escape(property_name)}["\']',
            re.IGNORECASE,
        )
        fallback_match = fallback_pattern.search(html)
        if fallback_match:
            return fallback_match.group(1).strip()
        return None
