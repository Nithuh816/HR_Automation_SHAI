"""Read-only reference lists for any authenticated internal user.

Unlike the HR-Head-only admin routers, these expose just id/name/role so other
roles (recruiters, TLs) can render and assign requisitions.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.department import Department
from app.models.enums import Role
from app.models.user import User

router = APIRouter(prefix="/api/v1/lookups", tags=["lookups"])

RECRUITER_ROLES = (Role.TA_RECRUITER, Role.TA_TL)


class DepartmentOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class UserOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    role: Role


@router.get("/departments", response_model=list[DepartmentOption])
def departments(db: SessionDep, _: CurrentUser) -> list[Department]:
    return list(db.scalars(select(Department).order_by(Department.name)))


@router.get("/users", response_model=list[UserOption])
def users(db: SessionDep, _: CurrentUser) -> list[User]:
    return list(db.scalars(select(User).where(User.is_active).order_by(User.name)))


@router.get("/recruiters", response_model=list[UserOption])
def recruiters(db: SessionDep, _: CurrentUser) -> list[User]:
    stmt = (
        select(User).where(User.is_active).where(User.role.in_(RECRUITER_ROLES)).order_by(User.name)
    )
    return list(db.scalars(stmt))
