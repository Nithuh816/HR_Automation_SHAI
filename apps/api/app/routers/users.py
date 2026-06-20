"""User administration (HR Head only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import SessionDep, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# Every route here requires the HR Head role.
HrHead = Annotated[User, Depends(require_roles(Role.HR_HEAD))]


@router.get("", response_model=list[UserRead])
def list_users(db: SessionDep, _: HrHead) -> list[User]:
    return list(db.scalars(select(User).order_by(User.name)))


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: SessionDep, _: HrHead) -> User:
    user = User(
        email=payload.email.lower(),
        name=payload.name,
        role=payload.role,
        team=payload.team,
        department_id=payload.department_id,
        manager_id=payload.manager_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already exists"
        ) from exc
    db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: SessionDep, _: HrHead) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(user_id: int, db: SessionDep, _: HrHead) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    user.is_active = False
    db.commit()
    db.refresh(user)
    return user
