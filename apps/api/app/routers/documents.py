"""Internal document management: list, fetch file, verify/reject, upload link."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Response
from sqlalchemy import select

from app.core import pii
from app.deps import CurrentUser, SessionDep
from app.integrations.storage import get_storage
from app.models.candidate import Candidate, CandidateApplication
from app.models.document import Document
from app.models.enums import ApplicationStatus, DocumentStatus, MagicLinkScope, Role
from app.schemas.candidate import MagicLinkResponse
from app.schemas.document import DocumentRead, DocumentReviewRequest
from app.services import documents as svc
from app.services import magic_links

router = APIRouter(prefix="/api/v1", tags=["documents"])

CAN_REVIEW = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER, Role.PR}
CAN_MANAGE = {Role.HR_HEAD, Role.TA_TL, Role.TA_RECRUITER}
UPLOAD_LINK_TTL = timedelta(days=14)


def _require(role: Role, allowed: set[Role]) -> None:
    if role not in allowed:
        raise HTTPException(status_code=403, detail="not permitted")


def _get_doc(db: SessionDep, doc_id: int) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    return doc


def _to_read(doc: Document) -> DocumentRead:
    extracted = json.loads(doc.extracted_json) if doc.extracted_json else None
    return DocumentRead(
        id=doc.id,
        candidate_id=doc.candidate_id,
        application_id=doc.application_id,
        document_type=doc.document_type,
        original_filename=doc.original_filename,
        content_type=doc.content_type,
        size_bytes=doc.size_bytes,
        status=doc.status,
        extracted=extracted,
        aadhaar_masked=svc.mask(pii.decrypt(doc.aadhaar_enc)),
        pan_masked=svc.mask(pii.decrypt(doc.pan_enc)),
        review_note=doc.review_note,
        uploaded_by_id=doc.uploaded_by_id,
        reviewed_by_id=doc.reviewed_by_id,
        reviewed_at=doc.reviewed_at,
        created_at=doc.created_at,
    )


@router.get("/candidates/{candidate_id}/documents", response_model=list[DocumentRead])
def list_documents(candidate_id: int, db: SessionDep, user: CurrentUser) -> list[DocumentRead]:
    _require(user.role, CAN_REVIEW)
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    rows = db.scalars(
        select(Document).where(Document.candidate_id == candidate_id).order_by(Document.id.desc())
    )
    return [_to_read(d) for d in rows]


@router.get("/documents/{doc_id}", response_model=DocumentRead)
def get_document(doc_id: int, db: SessionDep, user: CurrentUser) -> DocumentRead:
    _require(user.role, CAN_REVIEW)
    return _to_read(_get_doc(db, doc_id))


@router.get("/documents/{doc_id}/file")
def fetch_file(doc_id: int, db: SessionDep, user: CurrentUser) -> Response:
    """Stream the raw file behind authentication (kept out of JSON lists)."""
    _require(user.role, CAN_REVIEW)
    doc = _get_doc(db, doc_id)
    try:
        body = get_storage().get(doc.storage_key)
    except (FileNotFoundError, OSError) as exc:
        raise HTTPException(status_code=404, detail="file missing from storage") from exc
    return Response(
        content=body,
        media_type=doc.content_type,
        headers={"Content-Disposition": f'inline; filename="{doc.original_filename}"'},
    )


@router.post("/documents/{doc_id}/verify", response_model=DocumentRead)
def verify_document(doc_id: int, db: SessionDep, user: CurrentUser) -> DocumentRead:
    _require(user.role, CAN_REVIEW)
    doc = _get_doc(db, doc_id)
    doc.status = DocumentStatus.VERIFIED
    doc.reviewed_by_id = user.id
    doc.reviewed_at = datetime.now(UTC)
    db.commit()
    db.refresh(doc)
    return _to_read(doc)


@router.post("/documents/{doc_id}/reject", response_model=DocumentRead)
def reject_document(
    doc_id: int, payload: DocumentReviewRequest, db: SessionDep, user: CurrentUser
) -> DocumentRead:
    _require(user.role, CAN_REVIEW)
    doc = _get_doc(db, doc_id)
    doc.status = DocumentStatus.REJECTED
    doc.review_note = payload.note
    doc.reviewed_by_id = user.id
    doc.reviewed_at = datetime.now(UTC)
    db.commit()
    db.refresh(doc)
    return _to_read(doc)


@router.delete("/documents/{doc_id}", status_code=204)
def delete_document(doc_id: int, db: SessionDep, user: CurrentUser) -> None:
    _require(user.role, CAN_MANAGE)
    doc = _get_doc(db, doc_id)
    with contextlib.suppress(OSError):
        get_storage().delete(doc.storage_key)  # best-effort; still drop the row
    db.delete(doc)
    db.commit()


@router.post("/candidates/{candidate_id}/upload-link", response_model=MagicLinkResponse)
def create_upload_link(candidate_id: int, db: SessionDep, user: CurrentUser) -> MagicLinkResponse:
    _require(user.role, CAN_MANAGE)
    if db.get(Candidate, candidate_id) is None:
        raise HTTPException(status_code=404, detail="candidate not found")
    app = db.scalar(
        select(CandidateApplication)
        .where(CandidateApplication.candidate_id == candidate_id)
        .where(CandidateApplication.status == ApplicationStatus.ACTIVE)
        .order_by(CandidateApplication.id.desc())
    )
    if app is None:
        raise HTTPException(status_code=409, detail="candidate has no active application")
    token, link = magic_links.create_link(db, MagicLinkScope.DOC_UPLOAD, app.id, UPLOAD_LINK_TTL)
    db.commit()
    return MagicLinkResponse(url=magic_links.build_url(token, "upload"), expires_at=link.expires_at)
