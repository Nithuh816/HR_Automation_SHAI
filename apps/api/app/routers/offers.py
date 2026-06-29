"""Offer lifecycle: build, approve, send, and the printable letter."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy import select

from app.deps import CurrentUser, SessionDep
from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import (
    STAGE_ORDER,
    ApplicationStatus,
    MagicLinkScope,
    OfferStatus,
    Role,
    Stage,
)
from app.models.offer import Offer, OfferTemplate
from app.models.requisition import Requisition
from app.schemas.offer import (
    OfferCreate,
    OfferDetail,
    OfferSendResult,
    OfferUpdate,
    SalaryComponent,
)
from app.services import audit, magic_links, notifications, offers, pipeline

router = APIRouter(prefix="/api/v1", tags=["offers"])

CAN_BUILD = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER}
OFFER_LINK_TTL = timedelta(days=7)


def _require_build(role: Role) -> None:
    if role not in CAN_BUILD:
        raise HTTPException(status_code=403, detail="TA members only")


def _get_offer(db: SessionDep, offer_id: int) -> Offer:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=404, detail="offer not found")
    return offer


def _context(db: SessionDep, offer: Offer) -> tuple[Candidate, Requisition]:
    app = db.get(CandidateApplication, offer.application_id)
    candidate = db.get(Candidate, app.candidate_id) if app else None
    req = db.get(Requisition, app.requisition_id) if app else None
    if app is None or candidate is None or req is None:
        raise HTTPException(status_code=404, detail="offer context missing")
    return candidate, req


def _detail(db: SessionDep, offer: Offer) -> OfferDetail:
    candidate, req = _context(db, offer)
    return OfferDetail(
        id=offer.id,
        application_id=offer.application_id,
        template_id=offer.template_id,
        designation=offer.designation,
        annual_ctc=offer.annual_ctc,
        joining_date=offer.joining_date,
        notes=offer.notes,
        status=offer.status,
        created_by_id=offer.created_by_id,
        approved_by_id=offer.approved_by_id,
        approved_at=offer.approved_at,
        sent_at=offer.sent_at,
        responded_at=offer.responded_at,
        decline_reason=offer.decline_reason,
        candidate_id=candidate.id,
        candidate_name=candidate.name,
        requisition_id=req.id,
        requisition_title=req.title,
        components=[SalaryComponent(**c) for c in offers.load_components(offer.components_json)],
    )


def _letter_html(db: SessionDep, offer: Offer) -> tuple[str, str]:
    """Return (subject, html) for the rendered offer letter."""
    candidate, _ = _context(db, offer)
    template = db.get(OfferTemplate, offer.template_id) if offer.template_id else None
    subject = template.subject if template else f"Offer of Employment — {offer.designation}"
    body_md = template.body_md if template else offers.DEFAULT_TEMPLATE_BODY
    body = offers.render_letter_body(
        body_md,
        candidate_name=candidate.name,
        designation=offer.designation,
        annual_ctc=offer.annual_ctc,
        joining_date=offer.joining_date,
    )
    html = offers.render_letter_html(
        subject=subject,
        body=body,
        components=offers.load_components(offer.components_json),
    )
    return subject, html


@router.post("/applications/{app_id}/offers", response_model=OfferDetail, status_code=201)
def create_offer(
    app_id: int, payload: OfferCreate, db: SessionDep, user: CurrentUser
) -> OfferDetail:
    _require_build(user.role)
    app = db.get(CandidateApplication, app_id)
    if app is None:
        raise HTTPException(status_code=404, detail="application not found")
    if app.status != ApplicationStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="application is not active")
    if db.scalar(
        select(Offer)
        .where(Offer.application_id == app_id)
        .where(Offer.status.notin_([OfferStatus.DECLINED, OfferStatus.REVOKED]))
    ):
        raise HTTPException(status_code=409, detail="an active offer already exists")
    if payload.template_id is not None and db.get(OfferTemplate, payload.template_id) is None:
        raise HTTPException(status_code=422, detail="unknown template")

    req = db.get(Requisition, app.requisition_id)
    if req is None:
        raise HTTPException(status_code=404, detail="requisition not found")
    components = offers.compute_breakdown(payload.annual_ctc)
    offer = Offer(
        application_id=app_id,
        template_id=payload.template_id,
        designation=payload.designation or req.title,
        annual_ctc=payload.annual_ctc,
        components_json=offers.dump_components(components),
        joining_date=payload.joining_date,
        notes=payload.notes,
        created_by_id=user.id,
    )
    db.add(offer)
    db.flush()
    if STAGE_ORDER.index(Stage.OFFER) > STAGE_ORDER.index(app.stage):
        pipeline.set_stage(app, Stage.OFFER)
    audit.record(
        db,
        actor=user,
        action="offer.created",
        entity_type="offer",
        entity_id=offer.id,
        summary=f"{offer.designation} · ₹{offer.annual_ctc:,}",
    )
    db.commit()
    db.refresh(offer)
    return _detail(db, offer)


@router.get("/offers", response_model=list[OfferDetail])
def list_offers(db: SessionDep, _: CurrentUser) -> list[OfferDetail]:
    rows = db.scalars(select(Offer).order_by(Offer.id.desc()))
    return [_detail(db, o) for o in rows]


@router.get("/applications/{app_id}/offers", response_model=list[OfferDetail])
def list_application_offers(app_id: int, db: SessionDep, _: CurrentUser) -> list[OfferDetail]:
    if db.get(CandidateApplication, app_id) is None:
        raise HTTPException(status_code=404, detail="application not found")
    rows = db.scalars(select(Offer).where(Offer.application_id == app_id).order_by(Offer.id.desc()))
    return [_detail(db, o) for o in rows]


@router.get("/offers/{offer_id}", response_model=OfferDetail)
def get_offer(offer_id: int, db: SessionDep, _: CurrentUser) -> OfferDetail:
    return _detail(db, _get_offer(db, offer_id))


@router.patch("/offers/{offer_id}", response_model=OfferDetail)
def update_offer(
    offer_id: int, payload: OfferUpdate, db: SessionDep, user: CurrentUser
) -> OfferDetail:
    _require_build(user.role)
    offer = _get_offer(db, offer_id)
    if offer.status != OfferStatus.DRAFT:
        raise HTTPException(status_code=409, detail="only draft offers can be edited")
    if payload.template_id is not None and db.get(OfferTemplate, payload.template_id) is None:
        raise HTTPException(status_code=422, detail="unknown template")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(offer, field, value)
    if "annual_ctc" in data:
        offer.components_json = offers.dump_components(offers.compute_breakdown(offer.annual_ctc))
    db.commit()
    db.refresh(offer)
    return _detail(db, offer)


@router.post("/offers/{offer_id}/submit", response_model=OfferDetail)
def submit_offer(offer_id: int, db: SessionDep, user: CurrentUser) -> OfferDetail:
    _require_build(user.role)
    offer = _get_offer(db, offer_id)
    if offer.status != OfferStatus.DRAFT:
        raise HTTPException(status_code=409, detail="offer is not a draft")
    offer.status = OfferStatus.PENDING_APPROVAL
    audit.record(db, actor=user, action="offer.submitted", entity_type="offer", entity_id=offer.id)
    db.commit()
    db.refresh(offer)
    return _detail(db, offer)


@router.post("/offers/{offer_id}/approve", response_model=OfferDetail)
def approve_offer(offer_id: int, db: SessionDep, user: CurrentUser) -> OfferDetail:
    if user.role != Role.HR_HEAD:
        raise HTTPException(status_code=403, detail="only the HR Head may approve offers")
    offer = _get_offer(db, offer_id)
    if offer.status != OfferStatus.PENDING_APPROVAL:
        raise HTTPException(status_code=409, detail="offer is not awaiting approval")
    offer.status = OfferStatus.APPROVED
    offer.approved_by_id = user.id
    offer.approved_at = datetime.now(UTC)
    notifications.in_app(
        db,
        kind="offer_approved",
        recipient_user_id=offer.created_by_id,
        body=f"Your offer #{offer.id} was approved and is ready to send.",
        related_application_id=offer.application_id,
    )
    audit.record(db, actor=user, action="offer.approved", entity_type="offer", entity_id=offer.id)
    db.commit()
    db.refresh(offer)
    return _detail(db, offer)


@router.post("/offers/{offer_id}/send", response_model=OfferSendResult)
def send_offer(offer_id: int, db: SessionDep, user: CurrentUser) -> OfferSendResult:
    _require_build(user.role)
    offer = _get_offer(db, offer_id)
    if offer.status != OfferStatus.APPROVED:
        raise HTTPException(status_code=409, detail="offer must be approved before sending")
    token, link = magic_links.create_link(
        db, MagicLinkScope.OFFER, offer.application_id, OFFER_LINK_TTL
    )
    offer.status = OfferStatus.SENT
    offer.sent_at = datetime.now(UTC)
    url = magic_links.build_url(token, "offer")
    candidate, _ = _context(db, offer)
    notifications.offer_sent_email(
        db,
        application_id=offer.application_id,
        candidate_name=candidate.name,
        candidate_email=candidate.email,
        designation=offer.designation,
        url=url,
    )
    audit.record(db, actor=user, action="offer.sent", entity_type="offer", entity_id=offer.id)
    db.commit()
    db.refresh(offer)
    return OfferSendResult(
        url=url,
        expires_at=link.expires_at,
        offer=_detail(db, offer),
    )


@router.post("/offers/{offer_id}/revoke", response_model=OfferDetail)
def revoke_offer(offer_id: int, db: SessionDep, user: CurrentUser) -> OfferDetail:
    _require_build(user.role)
    offer = _get_offer(db, offer_id)
    if offer.status not in (OfferStatus.SENT, OfferStatus.APPROVED):
        raise HTTPException(status_code=409, detail="only an unaccepted offer can be revoked")
    offer.status = OfferStatus.REVOKED
    audit.record(db, actor=user, action="offer.revoked", entity_type="offer", entity_id=offer.id)
    db.commit()
    db.refresh(offer)
    return _detail(db, offer)


@router.get("/offers/{offer_id}/letter", response_class=HTMLResponse)
def offer_letter(offer_id: int, db: SessionDep, _: CurrentUser) -> HTMLResponse:
    html = _letter_html(db, _get_offer(db, offer_id))[1]
    return HTMLResponse(content=html)


@router.get("/offers/{offer_id}/letter.pdf")
def offer_letter_pdf(offer_id: int, db: SessionDep, _: CurrentUser) -> Response:
    html = _letter_html(db, _get_offer(db, offer_id))[1]
    pdf = offers.html_to_pdf(html)
    if pdf is None:
        raise HTTPException(
            status_code=501,
            detail="PDF rendering unavailable (WeasyPrint not installed); use Print to PDF.",
        )
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="offer-{offer_id}.pdf"'},
    )
