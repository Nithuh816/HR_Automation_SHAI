"""Read-only reference lists for any authenticated internal user.

Unlike the HR-Head-only admin routers, these expose just id/name/role so other
roles (recruiters, TLs) can render and assign requisitions.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.assessment import AssessmentTemplate
from app.models.department import Department
from app.models.document import DocumentChecklist
from app.models.enums import ChecklistType, DocumentType, InterviewRound, Role
from app.models.interview import RubricTemplate
from app.models.offer import OfferTemplate
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


class TemplateOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class RubricOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    round: InterviewRound


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


@router.get("/assessment-templates", response_model=list[TemplateOption])
def assessment_templates(db: SessionDep, _: CurrentUser) -> list[AssessmentTemplate]:
    stmt = (
        select(AssessmentTemplate)
        .where(AssessmentTemplate.is_active)
        .order_by(AssessmentTemplate.name)
    )
    return list(db.scalars(stmt))


@router.get("/rubrics", response_model=list[RubricOption])
def rubrics(db: SessionDep, _: CurrentUser) -> list[RubricTemplate]:
    stmt = select(RubricTemplate).where(RubricTemplate.is_active).order_by(RubricTemplate.name)
    return list(db.scalars(stmt))


@router.get("/offer-templates", response_model=list[TemplateOption])
def offer_templates(db: SessionDep, _: CurrentUser) -> list[OfferTemplate]:
    stmt = select(OfferTemplate).where(OfferTemplate.is_active).order_by(OfferTemplate.name)
    return list(db.scalars(stmt))


class ChecklistItemOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    document_type: DocumentType
    label: str
    required: bool


@router.get("/checklist", response_model=list[ChecklistItemOption])
def checklist(
    db: SessionDep, _: CurrentUser, checklist_type: ChecklistType
) -> list[DocumentChecklist]:
    stmt = (
        select(DocumentChecklist)
        .where(DocumentChecklist.checklist_type == checklist_type)
        .order_by(DocumentChecklist.position)
    )
    return list(db.scalars(stmt))
