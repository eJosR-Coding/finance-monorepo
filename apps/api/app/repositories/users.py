"""User data access (the admin, singular)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


def get_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email.strip().lower()))


def get_by_id(session: Session, user_id: int) -> User | None:
    return session.get(User, user_id)
