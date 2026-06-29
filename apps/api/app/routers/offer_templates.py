"""Offer-letter template administration (HR Head / TA TL)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import SessionDep, require_roles
from app.models.enums import Role
from app.models.offer import OfferTemplate
from app.models.user import User
from app.schemas.offer import (
    OfferTemplateCreate,
    OfferTemplateRead,
    OfferTemplateUpdate,
)

router = APIRouter(prefix="/api/v1/offer-templates", tags=["offer-templates"])

Manager = Annotated[User, Depends(require_roles(Role.HR_HEAD, Role.TA_TL))]


@router.post("", response_model=OfferTemplateRead, status_code=status.HTTP_201_CREATED)
def create_template(payload: OfferTemplateCreate, db: SessionDep, user: Manager) -> OfferTemplate:
    template = OfferTemplate(
        name=payload.name,
        subject=payload.subject,
        body_md=payload.body_md,
        created_by_id=user.id,
    )
    db.add(template)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="template name already exists") from exc
    db.refresh(template)
    return template


@router.get("", response_model=list[OfferTemplateRead])
def list_templates(db: SessionDep, _: Manager) -> list[OfferTemplate]:
    return list(db.scalars(select(OfferTemplate).order_by(OfferTemplate.name)))


@router.get("/{template_id}", response_model=OfferTemplateRead)
def get_template(template_id: int, db: SessionDep, _: Manager) -> OfferTemplate:
    template = db.get(OfferTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    return template


@router.patch("/{template_id}", response_model=OfferTemplateRead)
def update_template(
    template_id: int, payload: OfferTemplateUpdate, db: SessionDep, _: Manager
) -> OfferTemplate:
    template = db.get(OfferTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return template
