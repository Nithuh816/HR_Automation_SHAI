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
