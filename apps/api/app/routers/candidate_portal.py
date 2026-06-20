"""Candidate-facing pages — authenticated by magic-link token, no account.

All routes live under ``/api/v1/c`` and take a token in the path.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.deps import SessionDep
from app.models.candidate import (
    ApplicationFormL1,
    Candidate,
    CandidateApplication,
)
from app.models.enums import MagicLinkScope, Stage
from app.models.requisition import Requisition
from app.schemas.candidate import L1Context, L1Submit
from app.services import magic_links

router = APIRouter(prefix="/api/v1/c", tags=["candidate-portal"])


def _resolve(db: SessionDep, token: str) -> tuple[CandidateApplication, Candidate, Requisition]:
    try:
        link = magic_links.verify(db, token, MagicLinkScope.L1_APPLY)
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
    app, candidate, req = _resolve(db, token)
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
    app, candidate, req = _resolve(db, token)
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
    db.commit()

    return L1Context(
        candidate_name=candidate.name,
        requisition_title=req.title,
        already_submitted=True,
        payload=payload.payload,
    )
