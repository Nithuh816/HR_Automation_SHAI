"""Enumerations for identity and org structure.

Roles map onto the recruitment flow:
- ``HR_HEAD``      — triages requisitions, manages users/departments.
- ``TA_TL``        — Talent Acquisition Team Lead; L6 salary discussion.
- ``TA_RECRUITER`` — owns sourcing -> screening -> offer for assigned reqs.
- ``DEPT_LEAD``    — department Team Lead; L4 Technical Round 1 interviewer.
- ``DEPT_HEAD``    — department Head; L5 Technical Round 2 interviewer.
- ``PR``           — Post-Recruitment team; onboarding handoff into GreytHR.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    HR_HEAD = "hr_head"
    TA_TL = "ta_tl"
    TA_RECRUITER = "ta_recruiter"
    DEPT_LEAD = "dept_lead"
    DEPT_HEAD = "dept_head"
    PR = "pr"


class Team(StrEnum):
    TA = "ta"
    PR = "pr"
    MGMT = "mgmt"
    DEPT = "dept"


class RequisitionStatus(StrEnum):
    DRAFT = "draft"  # being prepared, not yet in triage
    SUBMITTED = "submitted"  # awaiting HR Head triage (the inbox)
    ASSIGNED = "assigned"  # a TA recruiter owns it; sourcing underway
    ON_HOLD = "on_hold"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Urgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Stage(StrEnum):
    """Ordered pipeline stages for a candidate application."""

    SOURCED = "sourced"
    L1_APPLICATION = "l1_application"
    L2_ASSESSMENT = "l2_assessment"
    L3_HR = "l3_hr"
    L4_TECH1 = "l4_tech1"
    L5_TECH2 = "l5_tech2"
    L6_SALARY = "l6_salary"
    OFFER = "offer"
    JOINED = "joined"


# Canonical ordering used to advance applications stage-by-stage.
STAGE_ORDER: tuple[Stage, ...] = (
    Stage.SOURCED,
    Stage.L1_APPLICATION,
    Stage.L2_ASSESSMENT,
    Stage.L3_HR,
    Stage.L4_TECH1,
    Stage.L5_TECH2,
    Stage.L6_SALARY,
    Stage.OFFER,
    Stage.JOINED,
)


class ApplicationStatus(StrEnum):
    ACTIVE = "active"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CandidateSource(StrEnum):
    LINKEDIN = "linkedin"
    NAUKRI = "naukri"
    REFERRAL = "referral"
    INSTITUTION = "institution"
    COLD_CALL = "cold_call"
    OTHER = "other"


class MagicLinkScope(StrEnum):
    L1_APPLY = "l1_apply"
    L2_ASSESSMENT = "l2_assessment"
    OFFER = "offer"
    DOC_UPLOAD = "doc_upload"


class AttemptStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


class InterviewRound(StrEnum):
    """Live interview rounds, each bound to a pipeline stage."""

    L3_HR = "l3_hr"
    L4_TECH1 = "l4_tech1"
    L5_TECH2 = "l5_tech2"
    L6_SALARY = "l6_salary"


# Each interview round maps onto the pipeline stage it gates.
ROUND_STAGE: dict[InterviewRound, Stage] = {
    InterviewRound.L3_HR: Stage.L3_HR,
    InterviewRound.L4_TECH1: Stage.L4_TECH1,
    InterviewRound.L5_TECH2: Stage.L5_TECH2,
    InterviewRound.L6_SALARY: Stage.L6_SALARY,
}


class InterviewMode(StrEnum):
    ONLINE = "online"  # Teams meeting
    IN_PERSON = "in_person"
    PHONE = "phone"


class InterviewStatus(StrEnum):
    SCHEDULED = "scheduled"
    RESCHEDULED = "rescheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class ScorecardDecision(StrEnum):
    STRONG_YES = "strong_yes"
    YES = "yes"
    NO = "no"
    STRONG_NO = "strong_no"


# Decisions that pass the candidate to the next stage; the rest reject.
POSITIVE_DECISIONS: frozenset[ScorecardDecision] = frozenset(
    {ScorecardDecision.STRONG_YES, ScorecardDecision.YES}
)


class OfferStatus(StrEnum):
    DRAFT = "draft"  # being built by a recruiter
    PENDING_APPROVAL = "pending_approval"  # awaiting HR Head sign-off
    APPROVED = "approved"  # signed off, ready to send
    SENT = "sent"  # delivered to the candidate (magic link live)
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"  # withdrawn internally after sending


class ChecklistType(StrEnum):
    FRESHER = "fresher"
    EXPERIENCED = "experienced"


class DocumentType(StrEnum):
    AADHAAR = "aadhaar"
    PAN = "pan"
    RESUME = "resume"
    MARKSHEET = "marksheet"
    EXPERIENCE_LETTER = "experience_letter"
    RELIEVING_LETTER = "relieving_letter"
    PAYSLIP = "payslip"
    PHOTO = "photo"
    BANK_PROOF = "bank_proof"
    OTHER = "other"


class DocumentStatus(StrEnum):
    PENDING = "pending"  # uploaded, awaiting auto/human check
    EXTRACTED = "extracted"  # auto-extraction succeeded, awaiting verification
    NEEDS_REVIEW = "needs_review"  # low/no confidence -> manual queue
    VERIFIED = "verified"  # a human confirmed it
    REJECTED = "rejected"
