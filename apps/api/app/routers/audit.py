"""Audit-log viewer (HR Head only)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.audit import AuditLog
from app.models.enums import Role
from app.schemas.audit import AuditRead

router = APIRouter(prefix="/api/v1/audit-log", tags=["audit"])


def _to_read(row: AuditLog) -> AuditRead:
    meta: dict[str, Any] | None = json.loads(row.meta_json) if row.meta_json else None
    return AuditRead(
        id=row.id,
        actor_user_id=row.actor_user_id,
        actor_label=row.actor_label,
        action=row.action,
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        summary=row.summary,
        meta=meta,
        created_at=row.created_at,
    )


@router.get("", response_model=list[AuditRead])
def list_audit(
    db: SessionDep,
    user: CurrentUser,
    entity_type: str | None = None,
    entity_id: int | None = None,
    action: str | None = None,
    actor_user_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditRead]:
    if user.role != Role.HR_HEAD:
        raise HTTPException(status_code=403, detail="the audit log is HR Head only")
    stmt = select(AuditLog).order_by(AuditLog.id.desc())
    if entity_type is not None:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    rows = db.scalars(stmt.limit(min(limit, 500)).offset(max(offset, 0))).all()
    return [_to_read(r) for r in rows]
