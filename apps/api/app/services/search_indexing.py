from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_summary import AISummary
from app.models.video import Video
from app.services.search_backend import SearchBackendUnavailable, get_search_backend

logger = logging.getLogger(__name__)


def ensure_search_index() -> None:
    get_search_backend().ensure_index()


def sync_video_search_documents(db: Session, *, video_id: UUID) -> None:
    video = _load_video_with_content(db, video_id=video_id)
    if not video:
        return

    documents = _build_documents(video)
    try:
        get_search_backend().replace_video_documents(video_id=str(video.id), documents=documents)
    except SearchBackendUnavailable:
        logger.warning("Search backend unavailable while syncing video %s.", video.id)


def delete_video_search_documents(*, video_id: UUID) -> None:
    try:
        get_search_backend().delete_video_documents(video_id=str(video_id))
    except SearchBackendUnavailable:
        logger.warning("Search backend unavailable while deleting video %s documents.", video_id)


def sync_space_search_documents(db: Session, *, space_id: UUID) -> None:
    stmt = select(Video.id).where(Video.space_id == space_id)
    for video_id in db.scalars(stmt).all():
        sync_video_search_documents(db, video_id=video_id)


def _load_video_with_content(db: Session, *, video_id: UUID) -> Video | None:
    stmt = (
        select(Video)
        .options(
            selectinload(Video.space),
            selectinload(Video.transcript_segments),
            selectinload(Video.key_concepts),
            selectinload(Video.key_takeaways),
            selectinload(Video.important_moments),
            selectinload(Video.notes),
            selectinload(Video.ai_summary),
        )
        .where(Video.id == video_id)
    )
    return db.scalar(stmt)


def _build_documents(video: Video) -> list[dict[str, object]]:
    if not video.space:
        return []

    shared = {
        "video_id": str(video.id),
        "video_title": video.title,
        "space_id": str(video.space.id),
        "space_title": video.space.title,
        "updated_at": video.updated_at.isoformat(),
        "completed": video.completed,
    }
    documents: list[dict[str, object]] = []
    owner_user_id = str(video.space.user_id)

    for segment in video.transcript_segments:
        documents.append(
            {
                "id": f"transcript:{segment.id}",
                "kind": "transcript",
                "user_id": owner_user_id,
                "timestamp": segment.start_time,
                "title": "Transcript section",
                "content": segment.text,
                "target_tab": "transcript",
                **shared,
            }
        )

    summary = video.ai_summary
    if isinstance(summary, AISummary):
        summary_parts = [
            summary.short_summary or "",
            summary.detailed_summary or "",
            summary.learning_notes or "",
            " ".join(item.content for item in video.key_takeaways),
        ]
        combined_summary = "\n\n".join(part for part in summary_parts if part.strip())
        if combined_summary.strip():
            documents.append(
                {
                    "id": f"summary:{summary.id}",
                    "kind": "summary",
                    "user_id": owner_user_id,
                    "timestamp": 0.0,
                    "title": "AI Summary",
                    "content": combined_summary,
                    "target_tab": "ai-summary",
                    **shared,
                }
            )

    for concept in video.key_concepts:
        documents.append(
            {
                "id": f"concept:{concept.id}",
                "kind": "concept",
                "user_id": owner_user_id,
                "timestamp": 0.0,
                "title": concept.concept,
                "content": concept.concept,
                "target_tab": "ai-summary",
                **shared,
            }
        )

    for moment in video.important_moments:
        documents.append(
            {
                "id": f"important_moment:{moment.id}",
                "kind": "important_moment",
                "user_id": owner_user_id,
                "timestamp": moment.timestamp,
                "title": moment.title,
                "content": moment.description,
                "target_tab": "ai-summary",
                **shared,
            }
        )

    for note in video.notes:
        note_content = "\n\n".join(
            part for part in [(note.title or "").strip(), note.content.strip()] if part
        )
        if not note_content:
            continue
        documents.append(
            {
                "id": f"note:{note.id}",
                "kind": "note",
                "user_id": str(note.user_id),
                "timestamp": note.anchor_timestamp or 0.0,
                "title": note.title or "Personal note",
                "content": note_content,
                "target_tab": "notes",
                **shared,
            }
        )

    return documents