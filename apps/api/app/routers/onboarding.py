"""Onboarding queue and the GreytHR handoff (M8).

The Post-Recruitment (PR) team owns this stage; the HR Head may also act.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.integrations.greythr import GreytHRError
from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import OfferStatus, OnboardingStatus, Role
from app.models.offer import Offer
from app.models.onboarding import OnboardingHandoff
from app.models.requisition import Requisition
from app.schemas.onboarding import OnboardingDetail, OnboardingQueueItem
from app.services import onboarding

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

CAN_ONBOARD = {Role.PR, Role.HR_HEAD}


def _require_onboard(role: Role) -> None:
    if role not in CAN_ONBOARD:
        raise HTTPException(status_code=403, detail="Post-Recruitment team only")


def _detail(db: SessionDep, handoff: OnboardingHandoff) -> OnboardingDetail:
    app = db.get(CandidateApplication, handoff.application_id)
    candidate = db.get(Candidate, app.candidate_id) if app else None
    req = db.get(Requisition, app.requisition_id) if app else None
    offer = onboarding.accepted_offer_for(db, handoff.application_id) if app else None
    if app is None or candidate is None or req is None or offer is None:
        raise HTTPException(status_code=404, detail="onboarding context missing")
    required, verified = onboarding.document_progress(db, candidate)
    return OnboardingDetail(
        id=handoff.id,
        application_id=handoff.application_id,
        status=handoff.status,
        greythr_employee_id=handoff.greythr_employee_id,
        retries=handoff.retries,
        last_error=handoff.last_error,
        pushed_at=handoff.pushed_at,
        joined_at=handoff.joined_at,
        created_by_id=handoff.created_by_id,
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        requisition_id=req.id,
        requisition_title=req.title,
        designation=offer.designation,
        annual_ctc=offer.annual_ctc,
        joining_date=offer.joining_date,
        documents_required=required,
        documents_verified=verified,
    )


@router.get("/queue", response_model=list[OnboardingQueueItem])
def onboarding_queue(db: SessionDep, user: CurrentUser) -> list[OnboardingQueueItem]:
    _require_onboard(user.role)
    accepted = db.scalars(
        select(Offer).where(Offer.status == OfferStatus.ACCEPTED).order_by(Offer.id.desc())
    ).all()
    items: list[OnboardingQueueItem] = []
    for offer in accepted:
        app = db.get(CandidateApplication, offer.application_id)
        if app is None:
            continue
        candidate = db.get(Candidate, app.candidate_id)
        req = db.get(Requisition, app.requisition_id)
        if candidate is None or req is None:
            continue
        handoff = onboarding.get_handoff(db, app.id)
        required, verified = onboarding.document_progress(db, candidate)
        items.append(
            OnboardingQueueItem(
                application_id=app.id,
                candidate_id=candidate.id,
                candidate_name=candidate.name,
                requisition_id=req.id,
                requisition_title=req.title,
                designation=offer.designation,
                joining_date=offer.joining_date,
                offer_status=offer.status,
                handoff_id=handoff.id if handoff else None,
                handoff_status=handoff.status if handoff else None,
                greythr_employee_id=handoff.greythr_employee_id if handoff else None,
                documents_required=required,
                documents_verified=verified,
            )
        )
    return items


@router.get("/{handoff_id}", response_model=OnboardingDetail)
def get_onboarding(handoff_id: int, db: SessionDep, user: CurrentUser) -> OnboardingDetail:
    _require_onboard(user.role)
    handoff = db.get(OnboardingHandoff, handoff_id)
    if handoff is None:
        raise HTTPException(status_code=404, detail="handoff not found")
    return _detail(db, handoff)


@router.post("/applications/{app_id}/push", response_model=OnboardingDetail)
def push_to_greythr(app_id: int, db: SessionDep, user: CurrentUser) -> OnboardingDetail:
    _require_onboard(user.role)
    app = db.get(CandidateApplication, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="application not found")
    if onboarding.accepted_offer_for(db, app_id) is None:
        raise HTTPException(status_code=409, detail="no accepted offer for this application")
    try:
        handoff = onboarding.push(db, app, user.id)
    except GreytHRError as exc:
        raise HTTPException(status_code=502, detail=f"GreytHR push failed: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _detail(db, handoff)


@router.post("/{handoff_id}/confirm-joining", response_model=OnboardingDetail)
def confirm_joining(handoff_id: int, db: SessionDep, user: CurrentUser) -> OnboardingDetail:
    _require_onboard(user.role)
    handoff = db.get(OnboardingHandoff, handoff_id)
    if handoff is None:
        raise HTTPException(status_code=404, detail="handoff not found")
    if handoff.status not in (OnboardingStatus.PUSHED, OnboardingStatus.JOINED):
        raise HTTPException(status_code=409, detail="employee must be pushed to GreytHR first")
    return _detail(db, onboarding.confirm_joining(db, handoff))
