from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ai_summary import AISummaryJobRead
from app.services.learning_intelligence import LearningInsightsService

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=AISummaryJobRead)
def get_ai_summary_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISummaryJobRead:
    return LearningInsightsService(db).get_job_for_user(job_id=job_id, user_id=current_user.id)