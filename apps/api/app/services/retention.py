"""DPDPA retention: anonymise rejected-candidate PII after a configurable window.

Hired candidates and anyone with an active application are never purged. The
operation is idempotent — a candidate is skipped once ``redacted_at`` is set.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.storage import get_storage
from app.models.candidate import Candidate, CandidateApplication
from app.models.document import Document
from app.models.enums import ApplicationStatus, Stage

log = structlog.get_logger()


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def redact_candidate(db: Session, candidate: Candidate, now: datetime) -> None:
    candidate.name = "Redacted Candidate"
    candidate.email = f"redacted+{candidate.id}@example.invalid"
    candidate.phone = None
    candidate.location = None
    candidate.current_company = None
    candidate.referred_by = None
    candidate.resume_url = None
    candidate.redacted_at = now
    storage = get_storage()
    for doc in db.scalars(select(Document).where(Document.candidate_id == candidate.id)):
        doc.aadhaar_enc = None
        doc.pan_enc = None
        doc.bank_account_enc = None
        doc.extracted_json = None
        if doc.storage_key:
            try:
                storage.delete(doc.storage_key)
            except Exception as exc:
                log.warning("retention.delete_failed", key=doc.storage_key, error=str(exc))
            doc.storage_key = ""


def is_purgeable(db: Session, candidate: Candidate, cutoff: datetime) -> bool:
    apps = db.scalars(
        select(CandidateApplication).where(CandidateApplication.candidate_id == candidate.id)
    ).all()
    if not apps:
        return False
    if any(a.status == ApplicationStatus.ACTIVE for a in apps):
        return False
    if any(a.stage == Stage.JOINED for a in apps):
        return False
    if not any(a.status == ApplicationStatus.REJECTED for a in apps):
        return False
    last_activity = max(_aware(a.updated_at) for a in apps)
    return last_activity < cutoff


def purge_rejected(db: Session, *, now: datetime, retention_days: int) -> int:
    """Redact every eligible rejected candidate. Returns the number redacted."""
    cutoff = now - timedelta(days=retention_days)
    candidates = db.scalars(select(Candidate).where(Candidate.redacted_at.is_(None))).all()
    count = 0
    for candidate in candidates:
        if is_purgeable(db, candidate, cutoff):
            redact_candidate(db, candidate, now)
            count += 1
    db.commit()
    return count
