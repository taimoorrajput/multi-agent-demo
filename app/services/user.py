from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, data: UserCreate) -> User:
    existing = db.scalar(select(User).where(User.email == data.email))
    if existing is not None:
        raise ApiError(409, "USER_EMAIL_TAKEN", f"Email '{data.email}' is already taken")

    user = User(email=data.email, name=data.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ApiError(404, "USER_NOT_FOUND", f"User {user_id} not found")
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User)))
