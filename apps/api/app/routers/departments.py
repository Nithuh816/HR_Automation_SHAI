"""Department administration (HR Head only)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import SessionDep, require_roles
from app.models.department import Department
from app.models.enums import Role
from app.models.user import User
from app.schemas.department import DepartmentCreate, DepartmentRead, DepartmentUpdate

router = APIRouter(prefix="/api/v1/departments", tags=["departments"])

HrHead = Annotated[User, Depends(require_roles(Role.HR_HEAD))]


def _validate_head(db: SessionDep, head_user_id: int | None) -> None:
    if head_user_id is not None and db.get(User, head_user_id) is None:
        raise HTTPException(
            status_code=422,
            detail="head_user_id does not reference an existing user",
        )


@router.get("", response_model=list[DepartmentRead])
def list_departments(db: SessionDep, _: HrHead) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)))


@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(payload: DepartmentCreate, db: SessionDep, _: HrHead) -> Department:
    _validate_head(db, payload.head_user_id)
    dept = Department(name=payload.name, head_user_id=payload.head_user_id)
    db.add(dept)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="department name already exists"
        ) from exc
    db.refresh(dept)
    return dept


@router.patch("/{dept_id}", response_model=DepartmentRead)
def update_department(
    dept_id: int, payload: DepartmentUpdate, db: SessionDep, _: HrHead
) -> Department:
    dept = db.get(Department, dept_id)
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="department not found")
    data = payload.model_dump(exclude_unset=True)
    if "head_user_id" in data:
        _validate_head(db, data["head_user_id"])
    for field, value in data.items():
        setattr(dept, field, value)
    db.commit()
    db.refresh(dept)
    return dept
