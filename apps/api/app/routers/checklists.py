"""Document-checklist administration (HR Head / TA TL)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.deps import SessionDep, require_roles
from app.models.document import DocumentChecklist
from app.models.enums import ChecklistType, Role
from app.models.user import User
from app.schemas.document import (
    ChecklistItemCreate,
    ChecklistItemRead,
    ChecklistItemUpdate,
)

router = APIRouter(prefix="/api/v1/checklists", tags=["checklists"])

Manager = Annotated[User, Depends(require_roles(Role.HR_HEAD, Role.TA_TL))]


@router.get("", response_model=list[ChecklistItemRead])
def list_items(
    db: SessionDep, _: Manager, checklist_type: ChecklistType | None = None
) -> list[DocumentChecklist]:
    stmt = select(DocumentChecklist)
    if checklist_type is not None:
        stmt = stmt.where(DocumentChecklist.checklist_type == checklist_type)
    stmt = stmt.order_by(DocumentChecklist.checklist_type, DocumentChecklist.position)
    return list(db.scalars(stmt))


@router.post("", response_model=ChecklistItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: ChecklistItemCreate, db: SessionDep, _: Manager) -> DocumentChecklist:
    item = DocumentChecklist(
        checklist_type=payload.checklist_type,
        document_type=payload.document_type,
        label=payload.label,
        required=payload.required,
        position=payload.position,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=ChecklistItemRead)
def update_item(
    item_id: int, payload: ChecklistItemUpdate, db: SessionDep, _: Manager
) -> DocumentChecklist:
    item = db.get(DocumentChecklist, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="checklist item not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: SessionDep, _: Manager) -> None:
    item = db.get(DocumentChecklist, item_id)
    if item is not None:
        db.delete(item)
        db.commit()
