from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.ingestion import IngestionJobRead
from app.services.ingestion_service import IngestionService

router = APIRouter()


@router.get("/jobs/{job_id}", response_model=IngestionJobRead)
def get_ingestion_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IngestionJobRead:
    return IngestionService(db).get_job_for_user(job_id=job_id, user_id=current_user.id)
