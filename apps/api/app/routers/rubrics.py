"""Rubric template administration (HR Head / TA TL)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import SessionDep, require_roles
from app.models.enums import Role
from app.models.interview import RubricCriterion, RubricTemplate
from app.models.user import User
from app.schemas.interview import (
    CriterionCreate,
    CriterionRead,
    RubricCreate,
    RubricDetail,
    RubricRead,
    RubricUpdate,
)

router = APIRouter(prefix="/api/v1/rubrics", tags=["rubrics"])

Manager = Annotated[User, Depends(require_roles(Role.HR_HEAD, Role.TA_TL))]


def _criteria(db: SessionDep, rubric_id: int) -> list[RubricCriterion]:
    stmt = (
        select(RubricCriterion)
        .where(RubricCriterion.rubric_template_id == rubric_id)
        .order_by(RubricCriterion.position.asc(), RubricCriterion.id.asc())
    )
    return list(db.scalars(stmt))


def _detail(db: SessionDep, rubric: RubricTemplate) -> RubricDetail:
    return RubricDetail(
        id=rubric.id,
        name=rubric.name,
        round=rubric.round,
        description=rubric.description,
        is_active=rubric.is_active,
        criteria=[CriterionRead.model_validate(c) for c in _criteria(db, rubric.id)],
    )


@router.post("", response_model=RubricRead, status_code=status.HTTP_201_CREATED)
def create_rubric(payload: RubricCreate, db: SessionDep, user: Manager) -> RubricTemplate:
    rubric = RubricTemplate(
        name=payload.name,
        round=payload.round,
        description=payload.description,
        created_by_id=user.id,
    )
    db.add(rubric)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="rubric name already exists") from exc
    db.refresh(rubric)
    return rubric


@router.get("", response_model=list[RubricRead])
def list_rubrics(db: SessionDep, _: Manager) -> list[RubricTemplate]:
    return list(db.scalars(select(RubricTemplate).order_by(RubricTemplate.name)))


@router.get("/{rubric_id}", response_model=RubricDetail)
def get_rubric(rubric_id: int, db: SessionDep, _: Manager) -> RubricDetail:
    rubric = db.get(RubricTemplate, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="rubric not found")
    return _detail(db, rubric)


@router.patch("/{rubric_id}", response_model=RubricRead)
def update_rubric(
    rubric_id: int, payload: RubricUpdate, db: SessionDep, _: Manager
) -> RubricTemplate:
    rubric = db.get(RubricTemplate, rubric_id)
    if rubric is None:
        raise HTTPException(status_code=404, detail="rubric not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rubric, field, value)
    db.commit()
    db.refresh(rubric)
    return rubric


@router.post(
    "/{rubric_id}/criteria", response_model=CriterionRead, status_code=status.HTTP_201_CREATED
)
def add_criterion(
    rubric_id: int, payload: CriterionCreate, db: SessionDep, _: Manager
) -> RubricCriterion:
    if db.get(RubricTemplate, rubric_id) is None:
        raise HTTPException(status_code=404, detail="rubric not found")
    criterion = RubricCriterion(
        rubric_template_id=rubric_id,
        label=payload.label,
        weight=payload.weight,
        max_score=payload.max_score,
        position=payload.position,
    )
    db.add(criterion)
    db.commit()
    db.refresh(criterion)
    return criterion


@router.delete(
    "/{rubric_id}/criteria/{criterion_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_criterion(
    rubric_id: int, criterion_id: int, db: SessionDep, _: Manager
) -> None:
    criterion = db.scalar(
        select(RubricCriterion)
        .where(RubricCriterion.id == criterion_id)
        .where(RubricCriterion.rubric_template_id == rubric_id)
    )
    if criterion is not None:
        db.delete(criterion)
        db.commit()
