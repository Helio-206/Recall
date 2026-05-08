from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.curriculum import (
    CurriculumManualOverrideUpdate,
    CurriculumReconstructionJobRead,
    CurriculumReconstructionRequest,
    SpaceCurriculumRead,
)
from app.services.curriculum_reconstruction import CurriculumReconstructionService

router = APIRouter()


@router.get("/spaces/{space_id}/curriculum", response_model=SpaceCurriculumRead)
def get_space_curriculum(
    space_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpaceCurriculumRead:
    return CurriculumReconstructionService(db).get_curriculum(
        space_id=space_id,
        user_id=current_user.id,
    )


@router.post(
    "/spaces/{space_id}/curriculum/rebuild",
    response_model=CurriculumReconstructionJobRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def rebuild_space_curriculum(
    space_id: UUID,
    payload: CurriculumReconstructionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumReconstructionJobRead:
    return CurriculumReconstructionService(db).request_rebuild(
        space_id=space_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.patch(
    "/spaces/{space_id}/curriculum/videos/{video_id}/override",
    response_model=SpaceCurriculumRead,
)
def update_curriculum_override(
    space_id: UUID,
    video_id: UUID,
    payload: CurriculumManualOverrideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpaceCurriculumRead:
    return CurriculumReconstructionService(db).update_manual_override(
        space_id=space_id,
        video_id=video_id,
        user_id=current_user.id,
        payload=payload,
    )


@router.get("/curriculum/jobs/{job_id}", response_model=CurriculumReconstructionJobRead)
def get_curriculum_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumReconstructionJobRead:
    return CurriculumReconstructionService(db).get_job_for_user(
        job_id=job_id,
        user_id=current_user.id,
    )