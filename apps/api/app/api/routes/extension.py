from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.extension import (
    ExtensionRecentSaveRead,
    ExtensionSaveAccepted,
    ExtensionSaveRequest,
    ExtensionSpaceRead,
)
from app.services.browser_extension import BrowserExtensionService

router = APIRouter()


@router.get("/spaces", response_model=list[ExtensionSpaceRead])
def list_extension_spaces(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExtensionSpaceRead]:
    return BrowserExtensionService(db).list_spaces(user_id=current_user.id)


@router.get("/recent-saves", response_model=list[ExtensionRecentSaveRead])
def list_recent_extension_saves(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ExtensionRecentSaveRead]:
    return BrowserExtensionService(db).list_recent_saves(user_id=current_user.id)


@router.post("/saves", response_model=ExtensionSaveAccepted, status_code=status.HTTP_202_ACCEPTED)
def save_extension_url(
    payload: ExtensionSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExtensionSaveAccepted:
    return BrowserExtensionService(db).save_url(user_id=current_user.id, payload=payload)