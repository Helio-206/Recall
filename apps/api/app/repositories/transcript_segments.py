from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.transcript_segment import TranscriptSegment


@dataclass(frozen=True)
class TranscriptSegmentDraft:
    start_time: float
    end_time: float
    text: str
    order_index: int


class TranscriptSegmentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_video(self, video_id: UUID) -> list[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.video_id == video_id)
            .order_by(TranscriptSegment.order_index.asc())
        )
        return list(self.db.scalars(stmt).all())

    def replace_for_video(
        self,
        *,
        video_id: UUID,
        segments: list[TranscriptSegmentDraft],
    ) -> list[TranscriptSegment]:
        self.db.execute(delete(TranscriptSegment).where(TranscriptSegment.video_id == video_id))
        rows = [
            TranscriptSegment(
                video_id=video_id,
                start_time=segment.start_time,
                end_time=segment.end_time,
                text=segment.text,
                order_index=segment.order_index,
            )
            for segment in segments
        ]
        self.db.add_all(rows)
        self.db.flush()
        return rows
