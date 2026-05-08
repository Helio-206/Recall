from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.extension_save_event import ExtensionSaveEvent


class ExtensionSaveEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        user_id: UUID,
        space_id: UUID,
        url: str,
        normalized_url: str,
        platform: str,
        source_type: str,
        status: str,
        page_title: str | None,
        page_description: str | None,
        browser: str | None,
        extension_version: str | None,
        page_metadata: dict,
    ) -> ExtensionSaveEvent:
        event = ExtensionSaveEvent(
            user_id=user_id,
            space_id=space_id,
            url=url,
            normalized_url=normalized_url,
            platform=platform,
            source_type=source_type,
            status=status,
            page_title=page_title,
            page_description=page_description,
            browser=browser,
            extension_version=extension_version,
            page_metadata=page_metadata,
        )
        self.db.add(event)
        self.db.flush()
        return event

    def count_for_user_since(self, *, user_id: UUID, created_after: datetime) -> int:
        stmt = select(func.count()).where(
            ExtensionSaveEvent.user_id == user_id,
            ExtensionSaveEvent.created_at >= created_after,
        )
        return int(self.db.scalar(stmt) or 0)

    def list_recent_for_user(self, *, user_id: UUID, limit: int) -> list[ExtensionSaveEvent]:
        stmt = (
            select(ExtensionSaveEvent)
            .where(ExtensionSaveEvent.user_id == user_id)
            .options(
                selectinload(ExtensionSaveEvent.space),
                selectinload(ExtensionSaveEvent.source),
                selectinload(ExtensionSaveEvent.ingestion_job),
            )
            .order_by(ExtensionSaveEvent.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def update_status(
        self,
        event: ExtensionSaveEvent,
        *,
        status: str,
        error_message: str | None = None,
        source_id: UUID | None = None,
        ingestion_job_id: UUID | None = None,
    ) -> ExtensionSaveEvent:
        event.status = status
        event.error_message = error_message
        if source_id is not None:
            event.source_id = source_id
        if ingestion_job_id is not None:
            event.ingestion_job_id = ingestion_job_id
        self.db.flush()
        return event