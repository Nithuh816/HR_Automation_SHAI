"""Pydantic schemas for users. ``ms_oid`` is never exposed."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.enums import Role, Team


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: Role
    team: Team
    department_id: int | None = None
    manager_id: int | None = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: str | None = None
    role: Role | None = None
    team: Team | None = None
    department_id: int | None = None
    manager_id: int | None = None
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
