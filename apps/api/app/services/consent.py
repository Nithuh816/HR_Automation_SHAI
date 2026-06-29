"""Recording and reading DPDPA consent (M11)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import CandidateApplication
from app.models.consent import Consent


def record(db: Session, *, application_id: int, purpose: str, text: str) -> Consent | None:
    """Persist a consent if one for this (application, purpose) isn't already on file."""
    if db.scalar(
        select(Consent)
        .where(Consent.application_id == application_id)
        .where(Consent.purpose == purpose)
    ):
        return None
    consent = Consent(
        application_id=application_id,
        purpose=purpose,
        text=text,
        given_at=datetime.now(UTC),
    )
    db.add(consent)
    db.flush()
    return consent


def for_candidate(db: Session, candidate_id: int) -> list[Consent]:
    app_ids = db.scalars(
        select(CandidateApplication.id).where(CandidateApplication.candidate_id == candidate_id)
    ).all()
    if not app_ids:
        return []
    return list(
        db.scalars(
            select(Consent).where(Consent.application_id.in_(app_ids)).order_by(Consent.id.desc())
        )
    )
