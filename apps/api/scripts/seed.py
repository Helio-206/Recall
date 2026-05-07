from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.space import LearningSpace
from app.models.user import User
from app.models.video import Video


def seed(db: Session) -> None:
    email = "demo@recall.dev"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return

    user = User(
        name="Recall Demo",
        email=email,
        password_hash=get_password_hash("recall-demo-123"),
    )
    space = LearningSpace(
        title="DevOps Engineering",
        description=(
            "A practical path through Linux, Docker, orchestration, and production systems."
        ),
        topic="Infrastructure",
        user=user,
    )
    space.videos = [
        Video(
            title="Linux File Permissions",
            thumbnail="https://img.youtube.com/vi/0D5nq3T8XFY/hqdefault.jpg",
            author="Engineering Notes",
            duration=936,
            url="https://www.youtube.com/watch?v=0D5nq3T8XFY",
            order_index=0,
            completed=True,
        ),
        Video(
            title="Docker Networking Deep Dive",
            thumbnail="https://img.youtube.com/vi/bKFMS5C4CG0/hqdefault.jpg",
            author="Learning Systems Lab",
            duration=1440,
            url="https://www.youtube.com/watch?v=bKFMS5C4CG0",
            order_index=1,
            completed=False,
        ),
        Video(
            title="Kubernetes Deployments Explained",
            thumbnail="https://img.youtube.com/vi/X48VuDVv0do/hqdefault.jpg",
            author="Field Guide",
            duration=1812,
            url="https://www.youtube.com/watch?v=X48VuDVv0do",
            order_index=2,
            completed=False,
        ),
    ]
    db.add(user)
    db.commit()


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed(session)
    finally:
        session.close()
