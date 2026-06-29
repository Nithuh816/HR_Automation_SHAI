"""Onboarding handoff logic: eligibility, GreytHR payload, push, joining."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.integrations.greythr import GreytHRError, get_greythr_client
from app.models.candidate import Candidate, CandidateApplication
from app.models.document import Document, DocumentChecklist
from app.models.enums import (
    ChecklistType,
    DocumentStatus,
    OfferStatus,
    OnboardingStatus,
    Stage,
)
from app.models.offer import Offer
from app.models.onboarding import OnboardingHandoff
from app.models.requisition import Requisition
from app.services import pipeline


def accepted_offer_for(db: Session, application_id: int) -> Offer | None:
    return db.scalar(
        select(Offer)
        .where(Offer.application_id == application_id)
        .where(Offer.status == OfferStatus.ACCEPTED)
        .order_by(Offer.id.desc())
    )


def document_progress(db: Session, candidate: Candidate) -> tuple[int, int]:
    """Return (required_count, verified_count) against the candidate's checklist."""
    checklist_type = ChecklistType.FRESHER if candidate.is_fresher else ChecklistType.EXPERIENCED
    required = (
        db.scalar(
            select(func.count())
            .select_from(DocumentChecklist)
            .where(DocumentChecklist.checklist_type == checklist_type)
            .where(DocumentChecklist.required.is_(True))
        )
        or 0
    )
    verified = (
        db.scalar(
            select(func.count(func.distinct(Document.document_type)))
            .where(Document.candidate_id == candidate.id)
            .where(Document.status == DocumentStatus.VERIFIED)
        )
        or 0
    )
    return int(required), int(verified)


def build_payload(
    app: CandidateApplication, candidate: Candidate, offer: Offer, req: Requisition
) -> dict[str, Any]:
    """The new-hire record sent to GreytHR (idempotency keyed on application_id)."""
    return {
        "application_id": app.id,
        "employee": {
            "full_name": candidate.name,
            "email": candidate.email,
            "phone": candidate.phone,
            "designation": offer.designation,
            "department_id": req.department_id,
            "annual_ctc": offer.annual_ctc,
            "date_of_joining": offer.joining_date.isoformat(),
        },
        "source": "HR_Automation_SHAI",
    }


def get_handoff(db: Session, application_id: int) -> OnboardingHandoff | None:
    return db.scalar(
        select(OnboardingHandoff).where(OnboardingHandoff.application_id == application_id)
    )


def push(db: Session, app: CandidateApplication, user_id: int) -> OnboardingHandoff:
    """Push the new hire to GreytHR. Idempotent; raises GreytHRError on failure."""
    candidate = db.get(Candidate, app.candidate_id)
    req = db.get(Requisition, app.requisition_id)
    offer = accepted_offer_for(db, app.id)
    if candidate is None or req is None or offer is None:
        raise ValueError("application is not ready for onboarding")

    handoff = get_handoff(db, app.id)
    if handoff is None:
        handoff = OnboardingHandoff(application_id=app.id, created_by_id=user_id)
        db.add(handoff)
    elif handoff.status in (OnboardingStatus.PUSHED, OnboardingStatus.JOINED):
        return handoff  # already done — idempotent no-op

    payload = build_payload(app, candidate, offer, req)
    try:
        employee_id = get_greythr_client().create_employee(payload)
    except GreytHRError as exc:
        handoff.status = OnboardingStatus.FAILED
        handoff.retries += 1
        handoff.last_error = str(exc)
        db.commit()
        db.refresh(handoff)
        raise

    handoff.greythr_employee_id = employee_id
    handoff.status = OnboardingStatus.PUSHED
    handoff.payload_json = json.dumps(payload)
    handoff.last_error = None
    handoff.pushed_at = datetime.now(UTC)
    db.commit()
    db.refresh(handoff)
    return handoff


def confirm_joining(db: Session, handoff: OnboardingHandoff) -> OnboardingHandoff:
    """Mark the hire as joined and advance the application to the final stage."""
    app = db.get(CandidateApplication, handoff.application_id)
    if app is None:
        raise ValueError("application missing")
    handoff.status = OnboardingStatus.JOINED
    handoff.joined_at = datetime.now(UTC)
    pipeline.set_stage(app, Stage.JOINED)
    db.commit()
    db.refresh(handoff)
    return handoff
