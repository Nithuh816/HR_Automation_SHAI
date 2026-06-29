"""Schemas for the audit-log viewer."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditRead(BaseModel):
    id: int
    actor_user_id: int | None
    actor_label: str
    action: str
    entity_type: str
    entity_id: int | None
    summary: str | None
    meta: dict[str, Any] | None
    created_at: datetime
