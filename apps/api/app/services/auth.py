from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.auth import GoogleLoginRequest, LoginRequest, RegisterRequest, TokenResponse


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = get_settings()

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

    def login_with_google(self, payload: GoogleLoginRequest) -> TokenResponse:
        allowed_client_ids = self.settings.google_oauth_client_id_list
        if not allowed_client_ids:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google login is not configured.",
            )

        token_data = self._verify_google_id_token(payload.id_token)
        token_audience = str(token_data.get("aud") or "")
        if token_audience not in allowed_client_ids:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google token was issued for a different application.",
            )

        email = str(token_data.get("email") or "").strip().lower()
        if not email or not token_data.get("email_verified"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google account email is missing or not verified.",
            )

        user = self.users.get_by_email(email)
        if not user:
            full_name = str(token_data.get("name") or "").strip()
            user = self.users.create(
                name=full_name or email.split("@")[0],
                email=email,
                password_hash=get_password_hash(str(uuid4())),
            )
            self.db.commit()
            self.db.refresh(user)

        return self._build_token_response(user)

    @staticmethod
    def _verify_google_id_token(id_token: str) -> dict:
        try:
            from google.auth.transport.requests import Request
            from google.oauth2 import id_token as google_id_token
        except ImportError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google login dependencies are not installed.",
            ) from exc

        try:
            token_data = google_id_token.verify_oauth2_token(id_token, Request(), audience=None)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token.",
            ) from exc

        issuer = str(token_data.get("iss") or "")
        if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token issuer.",
            )

        return token_data

    @staticmethod
    def _build_token_response(user: User) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=access_token, user=user)
