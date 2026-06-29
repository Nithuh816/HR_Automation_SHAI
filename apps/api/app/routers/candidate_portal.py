"""Candidate-facing pages — authenticated by magic-link token, no account.

All routes live under ``/api/v1/c`` and take a token in the path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from sqlalchemy import select

from app.core import pii
from app.deps import SessionDep
from app.integrations.storage import get_storage
from app.models.assessment import (
    AssessmentAnswer,
    AssessmentAttempt,
    AssessmentTemplate,
)
from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
)
from app.models.document import Document, DocumentChecklist
from app.models.enums import (
    ApplicationStatus,
    AttemptStatus,
    ChecklistType,
    DocumentType,
    MagicLinkScope,
    OfferStatus,
    Stage,
)
from app.models.offer import Offer, OfferTemplate
from app.models.requisition import Requisition
from app.schemas.assessment import (
    AssessmentContext,
    AssessmentResult,
    AssessmentSubmit,
    PublicQuestion,
)
from app.schemas.candidate import L1Context, L1Submit
from app.schemas.document import (
    ChecklistItemPublic,
    DocUploadContext,
    UploadedDocPublic,
)
from app.schemas.offer import (
    OfferDeclineRequest,
    OfferPublicContext,
    OfferResponseResult,
    SalaryComponent,
)
from app.services import assessments, audit, magic_links, offers, pipeline
from app.services import consent as consent_svc
from app.services import documents as doc_svc

CONSENT_TEXT = (
    "I confirm the documents I upload are genuine and belong to me, and I consent "
    "to SHAI Health processing them for recruitment and onboarding under its privacy "
    "policy (DPDPA, 2023)."
)
MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter(prefix="/api/v1/c", tags=["candidate-portal"])


def _resolve(
    db: SessionDep, token: str, scope: MagicLinkScope
) -> tuple[CandidateApplication, Candidate, Requisition]:
    try:
        link = magic_links.verify(db, token, scope)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    app = db.get(CandidateApplication, link.application_id)
    candidate = db.get(Candidate, app.candidate_id) if app else None
    req = db.get(Requisition, app.requisition_id) if app else None
    if app is None or candidate is None or req is None:
        raise HTTPException(status_code=404, detail="application not found")
    return app, candidate, req


@router.get("/l1/{token}", response_model=L1Context)
def get_l1_form(token: str, db: SessionDep) -> L1Context:
    app, candidate, req = _resolve(db, token, MagicLinkScope.L1_APPLY)
    existing = db.scalar(
        select(ApplicationFormL1).where(ApplicationFormL1.application_id == app.id)
    )
    return L1Context(
        candidate_name=candidate.name,
        requisition_title=req.title,
        already_submitted=existing is not None,
        payload=json.loads(existing.payload_json) if existing else None,
    )


@router.post("/l1/{token}", response_model=L1Context)
def submit_l1_form(token: str, payload: L1Submit, db: SessionDep) -> L1Context:
    app, candidate, req = _resolve(db, token, MagicLinkScope.L1_APPLY)
    if db.scalar(select(ApplicationFormL1).where(ApplicationFormL1.application_id == app.id)):
        raise HTTPException(status_code=409, detail="form already submitted")

    form = ApplicationFormL1(
        application_id=app.id,
        payload_json=json.dumps(payload.payload),
        submitted_at=datetime.now(UTC),
    )
    db.add(form)
    # Submitting the L1 form moves a freshly sourced candidate into L1.
    if app.stage == Stage.SOURCED:
        app.stage = Stage.L1_APPLICATION
        app.stage_entered_at = datetime.now(UTC)
    # Single-use: burn the link.
    link = magic_links.verify(db, token, MagicLinkScope.L1_APPLY)
    magic_links.consume(link)
    audit.record(
        db,
        actor_label="candidate",
        action="application.l1_submitted",
        entity_type="application",
        entity_id=app.id,
    )
    db.commit()

    return L1Context(
        candidate_name=candidate.name,
        requisition_title=req.title,
        already_submitted=True,
        payload=payload.payload,
    )


def _latest_attempt(db: SessionDep, application_id: int) -> AssessmentAttempt:
    attempt = db.scalar(
        select(AssessmentAttempt)
        .where(AssessmentAttempt.application_id == application_id)
        .order_by(AssessmentAttempt.id.desc())
    )
    if attempt is None:
        raise HTTPException(status_code=404, detail="no assessment for this link")
    return attempt


@router.get("/assessment/{token}", response_model=AssessmentContext)
def get_assessment(token: str, db: SessionDep) -> AssessmentContext:
    app, candidate, _ = _resolve(db, token, MagicLinkScope.L2_ASSESSMENT)
    attempt = _latest_attempt(db, app.id)
    template = db.get(AssessmentTemplate, attempt.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")

    # Start the clock on first open.
    if attempt.status == AttemptStatus.NOT_STARTED:
        now = datetime.now(UTC)
        attempt.status = AttemptStatus.IN_PROGRESS
        attempt.started_at = now
        attempt.expires_at = now + timedelta(minutes=template.duration_minutes)
        db.commit()

    questions = [
        PublicQuestion(id=q.id, text=q.text, options=assessments.options_of(q))
        for q in assessments.template_questions(db, template.id)
    ]
    return AssessmentContext(
        template_name=template.name,
        candidate_name=candidate.name,
        duration_minutes=template.duration_minutes,
        expires_at=attempt.expires_at or datetime.now(UTC),
        already_submitted=attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED),
        questions=questions,
    )


@router.post("/assessment/{token}", response_model=AssessmentResult)
def submit_assessment(token: str, payload: AssessmentSubmit, db: SessionDep) -> AssessmentResult:
    app, _, _ = _resolve(db, token, MagicLinkScope.L2_ASSESSMENT)
    attempt = _latest_attempt(db, app.id)
    if attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):
        raise HTTPException(status_code=409, detail="assessment already completed")

    valid_ids = {q.id for q in assessments.template_questions(db, attempt.template_id)}
    for ans in payload.answers:
        if ans.question_id in valid_ids:
            db.add(
                AssessmentAnswer(
                    attempt_id=attempt.id,
                    question_id=ans.question_id,
                    selected_index=ans.selected_index,
                )
            )
    db.flush()

    score_pct, passed = assessments.grade(db, attempt)
    attempt.score_pct = score_pct
    attempt.passed = passed
    attempt.status = AttemptStatus.SUBMITTED
    attempt.submitted_at = datetime.now(UTC)

    # Passing L2 advances the candidate to the HR round.
    if passed and app.stage in (
        Stage.SOURCED,
        Stage.L1_APPLICATION,
        Stage.L2_ASSESSMENT,
    ):
        app.stage = Stage.L3_HR
        app.stage_entered_at = datetime.now(UTC)

    link = magic_links.verify(db, token, MagicLinkScope.L2_ASSESSMENT)
    magic_links.consume(link)
    audit.record(
        db,
        actor_label="candidate",
        action="assessment.submitted",
        entity_type="application",
        entity_id=app.id,
        summary=f"Scored {score_pct:.0f}% — {'passed' if passed else 'did not pass'}",
        meta={"score_pct": score_pct, "passed": passed},
    )
    db.commit()
    return AssessmentResult(score_pct=score_pct, passed=passed)


def _offer_for(db: SessionDep, application_id: int) -> Offer:
    """The most recent offer issued on this application."""
    offer = db.scalar(
        select(Offer).where(Offer.application_id == application_id).order_by(Offer.id.desc())
    )
    if offer is None:
        raise HTTPException(status_code=404, detail="no offer for this link")
    return offer


def _build_offer_context(db: SessionDep, candidate: Candidate, offer: Offer) -> OfferPublicContext:
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
    components = offers.load_components(offer.components_json)
    html = offers.render_letter_html(subject=subject, body=body, components=components)
    return OfferPublicContext(
        candidate_name=candidate.name,
        designation=offer.designation,
        employer=offers.EMPLOYER_NAME,
        annual_ctc=offer.annual_ctc,
        joining_date=offer.joining_date,
        components=[SalaryComponent(**c) for c in components],
        subject=subject,
        letter_html=html,
        status=offer.status,
        already_responded=offer.status in (OfferStatus.ACCEPTED, OfferStatus.DECLINED),
    )


@router.get("/offer/{token}", response_model=OfferPublicContext)
def get_offer(token: str, db: SessionDep) -> OfferPublicContext:
    app, candidate, _ = _resolve(db, token, MagicLinkScope.OFFER)
    return _build_offer_context(db, candidate, _offer_for(db, app.id))


@router.post("/offer/{token}/accept", response_model=OfferResponseResult)
def accept_offer(token: str, db: SessionDep) -> OfferResponseResult:
    app, _, _ = _resolve(db, token, MagicLinkScope.OFFER)
    offer = _offer_for(db, app.id)
    if offer.status != OfferStatus.SENT:
        raise HTTPException(status_code=409, detail="this offer can no longer be accepted")
    offer.status = OfferStatus.ACCEPTED
    offer.responded_at = datetime.now(UTC)
    link = magic_links.verify(db, token, MagicLinkScope.OFFER)
    magic_links.consume(link)
    audit.record(
        db,
        actor_label="candidate",
        action="offer.accepted",
        entity_type="offer",
        entity_id=offer.id,
    )
    db.commit()
    return OfferResponseResult(status=offer.status)


@router.post("/offer/{token}/decline", response_model=OfferResponseResult)
def decline_offer(token: str, payload: OfferDeclineRequest, db: SessionDep) -> OfferResponseResult:
    app, _, _ = _resolve(db, token, MagicLinkScope.OFFER)
    offer = _offer_for(db, app.id)
    if offer.status != OfferStatus.SENT:
        raise HTTPException(status_code=409, detail="this offer can no longer be declined")
    offer.status = OfferStatus.DECLINED
    offer.responded_at = datetime.now(UTC)
    offer.decline_reason = payload.reason
    # Declining an offer ends the application.
    if app.status == ApplicationStatus.ACTIVE:
        pipeline.reject(app, payload.reason or "Offer declined by candidate")
    link = magic_links.verify(db, token, MagicLinkScope.OFFER)
    magic_links.consume(link)
    audit.record(
        db,
        actor_label="candidate",
        action="offer.declined",
        entity_type="offer",
        entity_id=offer.id,
        meta={"reason": payload.reason},
    )
    db.commit()
    return OfferResponseResult(status=offer.status)


def _checklist_type(candidate: Candidate) -> ChecklistType:
    return ChecklistType.FRESHER if candidate.is_fresher else ChecklistType.EXPERIENCED


def _upload_context(db: SessionDep, candidate: Candidate) -> DocUploadContext:
    ctype = _checklist_type(candidate)
    items = db.scalars(
        select(DocumentChecklist)
        .where(DocumentChecklist.checklist_type == ctype)
        .order_by(DocumentChecklist.position)
    )
    uploaded = db.scalars(
        select(Document).where(Document.candidate_id == candidate.id).order_by(Document.id.desc())
    )
    return DocUploadContext(
        candidate_name=candidate.name,
        checklist_type=ctype,
        consent_text=CONSENT_TEXT,
        items=[
            ChecklistItemPublic(document_type=i.document_type, label=i.label, required=i.required)
            for i in items
        ],
        uploaded=[
            UploadedDocPublic(
                id=d.id,
                document_type=d.document_type,
                original_filename=d.original_filename,
                status=d.status,
            )
            for d in uploaded
        ],
    )


@router.get("/upload/{token}", response_model=DocUploadContext)
def get_upload_portal(token: str, db: SessionDep) -> DocUploadContext:
    _, candidate, _ = _resolve(db, token, MagicLinkScope.DOC_UPLOAD)
    return _upload_context(db, candidate)


@router.post("/upload/{token}", response_model=DocUploadContext)
async def upload_document(
    token: str,
    db: SessionDep,
    document_type: Annotated[DocumentType, Form()],
    consent: Annotated[bool, Form()],
    file: Annotated[UploadFile, File()],
) -> DocUploadContext:
    app, candidate, _ = _resolve(db, token, MagicLinkScope.DOC_UPLOAD)
    if not consent:
        raise HTTPException(status_code=422, detail="consent is required to upload")
    consent_svc.record(db, application_id=app.id, purpose="documents", text=CONSENT_TEXT)
    body = await file.read()
    if not body:
        raise HTTPException(status_code=422, detail="empty file")
    if len(body) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="file too large (max 10 MB)")

    content_type = file.content_type or "application/octet-stream"
    analysis = doc_svc.analyze(document_type, content_type, body)
    doc = Document(
        candidate_id=candidate.id,
        application_id=app.id,
        document_type=document_type,
        original_filename=file.filename or "upload",
        storage_key="",
        content_type=content_type,
        size_bytes=len(body),
        status=analysis.status,
        extracted_json=doc_svc.dump_extracted(analysis.extracted),
        aadhaar_enc=pii.encrypt(analysis.aadhaar),
        pan_enc=pii.encrypt(analysis.pan),
    )
    db.add(doc)
    db.flush()  # assigns doc.id for the storage key
    doc.storage_key = doc_svc.storage_key(candidate.id, doc.id, doc.original_filename)
    get_storage().put(doc.storage_key, body, content_type)
    audit.record(
        db,
        actor_label="candidate",
        action="document.uploaded",
        entity_type="document",
        entity_id=doc.id,
        summary=document_type.value,
    )
    # The upload link is intentionally multi-use until it expires.
    db.commit()
    return _upload_context(db, candidate)
