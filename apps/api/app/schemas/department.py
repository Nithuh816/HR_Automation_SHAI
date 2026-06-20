"""Pydantic schemas for departments."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DepartmentBase(BaseModel):
    name: str
    head_user_id: int | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = None
    head_user_id: int | None = None


class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
