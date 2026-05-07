from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.space import LearningSpace


class LearningSpaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: UUID) -> list[LearningSpace]:
        stmt = (
            select(LearningSpace)
            .where(LearningSpace.user_id == user_id)
            .options(selectinload(LearningSpace.videos))
            .order_by(LearningSpace.updated_at.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def get_for_user(self, *, space_id: UUID, user_id: UUID) -> LearningSpace | None:
        stmt = (
            select(LearningSpace)
            .where(LearningSpace.id == space_id, LearningSpace.user_id == user_id)
            .options(selectinload(LearningSpace.videos))
        )
        return self.db.scalar(stmt)

    def create(
        self,
        *,
        user_id: UUID,
        title: str,
        description: str | None,
        topic: str | None,
    ) -> LearningSpace:
        space = LearningSpace(
            user_id=user_id,
            title=title.strip(),
            description=description.strip() if description else None,
            topic=topic.strip() if topic else None,
        )
        self.db.add(space)
        self.db.flush()
        return space

    def delete(self, space: LearningSpace) -> None:
        self.db.delete(space)
        self.db.flush()
