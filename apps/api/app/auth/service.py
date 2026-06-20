"""User-resolution helpers shared by the dev stub and the SSO callback."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def get_active_user(db: Session, user_id: int) -> User | None:
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        return None
    return user
