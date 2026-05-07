from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: RegisterRequest) -> TokenResponse:
        existing_user = self.users.get_by_email(payload.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        user = self.users.create(
            name=payload.name,
            email=str(payload.email),
            password_hash=get_password_hash(payload.password),
        )
        self.db.commit()
        self.db.refresh(user)
        return self._build_token_response(user)

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self.users.get_by_email(str(payload.email))
        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return self._build_token_response(user)

    @staticmethod
    def _build_token_response(user: User) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=access_token, user=user)
