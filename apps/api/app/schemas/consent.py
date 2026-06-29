"""Schemas for DPDPA consent records (M11)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ConsentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int
    purpose: str
    text: str
    given_at: datetime
