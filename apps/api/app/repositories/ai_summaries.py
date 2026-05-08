from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.ai_summary import AISummary
from app.models.important_moment import ImportantMoment
from app.models.key_concept import KeyConcept
from app.models.key_takeaway import KeyTakeaway
from app.models.review_question import ReviewQuestion


class AISummaryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_for_video(self, video_id: UUID) -> AISummary | None:
        stmt = select(AISummary).where(AISummary.video_id == video_id).limit(1)
        return self.db.scalar(stmt)

    def get_or_create(self, *, video_id: UUID, prompt_version: str) -> AISummary:
        summary = self.get_for_video(video_id)
        if summary:
            return summary
        summary = AISummary(video_id=video_id, prompt_version=prompt_version)
        self.db.add(summary)
        self.db.flush()
        return summary

    def replace_children(
        self,
        *,
        video_id: UUID,
        key_concepts: list[tuple[str, float]],
        key_takeaways: list[str],
        review_questions: list[tuple[str, str]],
        important_moments: list[tuple[str, float, str]],
    ) -> None:
        self.db.execute(delete(KeyConcept).where(KeyConcept.video_id == video_id))
        self.db.execute(delete(KeyTakeaway).where(KeyTakeaway.video_id == video_id))
        self.db.execute(delete(ReviewQuestion).where(ReviewQuestion.video_id == video_id))
        self.db.execute(delete(ImportantMoment).where(ImportantMoment.video_id == video_id))

        self.db.add_all(
            [
                KeyConcept(video_id=video_id, concept=concept, relevance_score=relevance_score)
                for concept, relevance_score in key_concepts
            ]
        )
        self.db.add_all(
            [
                KeyTakeaway(video_id=video_id, content=content, order_index=index)
                for index, content in enumerate(key_takeaways)
            ]
        )
        self.db.add_all(
            [
                ReviewQuestion(
                    video_id=video_id,
                    question=question,
                    answer=answer,
                    order_index=index,
                )
                for index, (question, answer) in enumerate(review_questions)
            ]
        )
        self.db.add_all(
            [
                ImportantMoment(
                    video_id=video_id,
                    title=title,
                    timestamp=timestamp,
                    description=description,
                    order_index=index,
                )
                for index, (title, timestamp, description) in enumerate(important_moments)
            ]
        )
        self.db.flush()