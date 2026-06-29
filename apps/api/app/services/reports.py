"""Aggregation queries behind the dashboards & reports (M10).

All functions are read-only and return validated schema objects so routers stay
thin. Counts are computed at SHAI's scale (hundreds of rows), so simple grouped
queries are plenty.
"""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import (
    STAGE_ORDER,
    ApplicationStatus,
    CandidateSource,
    OfferStatus,
    RequisitionStatus,
    Role,
    Stage,
)
from app.models.offer import Offer
from app.models.requisition import Requisition
from app.models.user import User
from app.schemas.report import (
    DropOff,
    FunnelReport,
    FunnelStage,
    RecruiterPerformance,
    ReportSummary,
    SourceCount,
    TimeToFillReport,
    TimeToFillSample,
)

STAGE_LABELS: dict[Stage, str] = {
    Stage.SOURCED: "Sourced",
    Stage.L1_APPLICATION: "L1 Application",
    Stage.L2_ASSESSMENT: "L2 Assessment",
    Stage.L3_HR: "L3 HR",
    Stage.L4_TECH1: "L4 Tech 1",
    Stage.L5_TECH2: "L5 Tech 2",
    Stage.L6_SALARY: "L6 Salary",
    Stage.OFFER: "Offer",
    Stage.JOINED: "Joined",
}

SOURCE_LABELS: dict[CandidateSource, str] = {
    CandidateSource.LINKEDIN: "LinkedIn",
    CandidateSource.NAUKRI: "Naukri",
    CandidateSource.REFERRAL: "Referral",
    CandidateSource.INSTITUTION: "Institution",
    CandidateSource.COLD_CALL: "Cold call",
    CandidateSource.OTHER: "Other",
}

_OUTSTANDING_OFFERS = (
    OfferStatus.PENDING_APPROVAL,
    OfferStatus.APPROVED,
    OfferStatus.SENT,
)


def _count(db: Session, stmt: Select[tuple[int]]) -> int:
    return int(db.scalar(stmt) or 0)


def summary(db: Session) -> ReportSummary:
    return ReportSummary(
        open_requisitions=_count(
            db,
            select(func.count())
            .select_from(Requisition)
            .where(
                Requisition.status.in_([RequisitionStatus.SUBMITTED, RequisitionStatus.ASSIGNED])
            ),
        ),
        total_candidates=_count(db, select(func.count()).select_from(Candidate)),
        active_applications=_count(
            db,
            select(func.count())
            .select_from(CandidateApplication)
            .where(CandidateApplication.status == ApplicationStatus.ACTIVE),
        ),
        offers_outstanding=_count(
            db,
            select(func.count()).select_from(Offer).where(Offer.status.in_(_OUTSTANDING_OFFERS)),
        ),
        hires=_count(
            db,
            select(func.count())
            .select_from(CandidateApplication)
            .where(CandidateApplication.stage == Stage.JOINED),
        ),
    )


def funnel(db: Session) -> FunnelReport:
    rows = db.execute(
        select(CandidateApplication.stage, func.count()).group_by(CandidateApplication.stage)
    ).all()
    by_stage: dict[Stage, int] = {stage: int(count) for stage, count in rows}
    # "Reached stage X" = applications whose current stage is at or beyond X.
    cumulative = 0
    reached: dict[Stage, int] = {}
    for stage in reversed(STAGE_ORDER):
        cumulative += by_stage.get(stage, 0)
        reached[stage] = cumulative
    stages = [
        FunnelStage(stage=s.value, label=STAGE_LABELS[s], count=reached[s]) for s in STAGE_ORDER
    ]
    rejected = _count(
        db,
        select(func.count())
        .select_from(CandidateApplication)
        .where(CandidateApplication.status == ApplicationStatus.REJECTED),
    )
    return FunnelReport(stages=stages, rejected=rejected, total=sum(by_stage.values()))


def sources(db: Session) -> list[SourceCount]:
    rows = db.execute(select(Candidate.source, func.count()).group_by(Candidate.source)).all()
    return [
        SourceCount(source=src.value, label=SOURCE_LABELS[src], count=int(count))
        for src, count in rows
    ]


def drop_offs(db: Session) -> list[DropOff]:
    rejected = db.scalars(
        select(CandidateApplication).where(
            CandidateApplication.status == ApplicationStatus.REJECTED
        )
    ).all()
    counts: dict[Stage, int] = {}
    for app in rejected:
        stage = app.rejection_stage or app.stage
        counts[stage] = counts.get(stage, 0) + 1
    return [
        DropOff(stage=s.value, label=STAGE_LABELS[s], count=counts[s])
        for s in STAGE_ORDER
        if s in counts
    ]


def time_to_fill(db: Session) -> TimeToFillReport:
    joined = db.scalars(
        select(CandidateApplication).where(CandidateApplication.stage == Stage.JOINED)
    ).all()
    samples: list[TimeToFillSample] = []
    for app in joined:
        req = db.get(Requisition, app.requisition_id)
        if req is None:
            continue
        days = (app.stage_entered_at - req.created_at).days
        samples.append(
            TimeToFillSample(requisition_id=req.id, code=req.code, title=req.title, days=days)
        )
    average = round(sum(s.days for s in samples) / len(samples), 1) if samples else None
    return TimeToFillReport(average_days=average, samples=samples)


def recruiter_performance(db: Session) -> list[RecruiterPerformance]:
    recruiters = db.scalars(select(User).where(User.role == Role.TA_RECRUITER)).all()
    out: list[RecruiterPerformance] = []
    for rec in recruiters:
        candidates = _count(
            db,
            select(func.count()).select_from(Candidate).where(Candidate.created_by_id == rec.id),
        )
        offers = _count(
            db, select(func.count()).select_from(Offer).where(Offer.created_by_id == rec.id)
        )
        hires = _count(
            db,
            select(func.count())
            .select_from(CandidateApplication)
            .join(Candidate, Candidate.id == CandidateApplication.candidate_id)
            .where(Candidate.created_by_id == rec.id)
            .where(CandidateApplication.stage == Stage.JOINED),
        )
        out.append(
            RecruiterPerformance(
                recruiter_id=rec.id,
                recruiter_name=rec.name,
                candidates=candidates,
                offers=offers,
                hires=hires,
            )
        )
    return out
