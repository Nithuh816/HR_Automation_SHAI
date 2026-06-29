"""Append-only audit trail.

``record()`` does NOT commit — it joins the caller's transaction so the audit
row is written atomically with the action that triggered it (both commit, or
both roll back). Call it just before the handler's ``db.commit()``.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def record(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    actor: User | None = None,
    actor_label: str | None = None,
    summary: str | None = None,
    meta: dict[str, Any] | None = None,
) -> None:
    """Append an audit entry. ``actor`` is the internal user (None for candidate
    or system actions, in which case ``actor_label`` names the source)."""
    label = actor.name if actor is not None else (actor_label or "system")
    db.add(
        AuditLog(
            actor_user_id=actor.id if actor is not None else None,
            actor_label=label,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            summary=summary,
            meta_json=json.dumps(meta) if meta is not None else None,
        )
    )
