from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email.lower())
        return self.db.scalar(stmt)

    def create(self, *, name: str, email: str, password_hash: str) -> User:
        user = User(name=name.strip(), email=email.lower(), password_hash=password_hash)
        self.db.add(user)
        self.db.flush()
        return user
