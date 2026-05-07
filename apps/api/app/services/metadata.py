from dataclasses import dataclass
from hashlib import sha1
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class VideoMetadata:
    title: str
    thumbnail: str | None
    author: str | None
    duration: int | None
    url: str


class MetadataService:
    """Phase 1 metadata extraction.

    This deliberately avoids downloads, transcripts, Whisper, and embeddings. For YouTube URLs it
    derives a thumbnail from the video id; everything else is stable mocked metadata.
    """

    lesson_titles = [
        "Systems Thinking for Builders",
        "Docker Networking Deep Dive",
        "Kubernetes Deployments Explained",
        "Linux File Permissions",
        "Designing Durable APIs",
        "Async Workflows in Practice",
    ]

    authors = [
        "Recall Import",
        "Engineering Notes",
        "Learning Systems Lab",
        "Field Guide",
    ]

    def extract(self, *, url: str, title_override: str | None = None) -> VideoMetadata:
        video_id = self._extract_youtube_id(url)
        digest = sha1(url.encode("utf-8")).hexdigest()
        title = title_override or self.lesson_titles[int(digest[0], 16) % len(self.lesson_titles)]
        duration = 360 + (int(digest[1:5], 16) % 4200)
        thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None
        author = self.authors[int(digest[5], 16) % len(self.authors)]
        return VideoMetadata(
            title=title,
            thumbnail=thumbnail,
            author=author,
            duration=duration,
            url=url,
        )

    @staticmethod
    def _extract_youtube_id(url: str) -> str | None:
        parsed = urlparse(url)
        host = parsed.netloc.replace("www.", "")
        if host == "youtu.be":
            return parsed.path.strip("/") or None
        if host in {"youtube.com", "m.youtube.com"}:
            query_id = parse_qs(parsed.query).get("v", [None])[0]
            if query_id:
                return query_id
            if parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
                return parsed.path.split("/")[2] if len(parsed.path.split("/")) > 2 else None
        return None
