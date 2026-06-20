"""Idempotent seed of SHAI departments and app users.

Run with:  ``python -m app.seed``

Data is derived from the SHAI employee directory (Active List 14-Jun-2026).
NOTE: emails are PLACEHOLDERS (``first.last@shaihealth.com``) — real addresses
and Microsoft SSO identities are wired in M1b. Roles for the HR/TA/PR staff are
inferred from designation + seniority; correct any line below and re-run.
"""

from __future__ import annotations

import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.department import Department
from app.models.enums import RequisitionStatus, Role, Team, Urgency
from app.models.requisition import Requisition
from app.models.user import User
from app.services.requisitions import make_code

EMAIL_DOMAIN = "shaihealth.com"

# Hiring departments (normalized from 25 raw labels). (name, head employee name)
DEPARTMENTS: list[tuple[str, str | None]] = [
    ("Transactions - Coding", "MosesDevanbu Sasikumar RE"),
    ("RCM", "Charles Sundarraj"),
    ("Quality Assurance", "Prabhu V"),
    ("Utilization Management", None),
    ("Training & Development", "S Raj Mohan Babu"),
    ("HCC", None),
    ("Business Development", "Prakash K"),
    ("Software", "Suresh Reddy K"),
    ("Network & IT Infra", "Shrikant Subhash Jain"),
    ("Admin", None),
    ("Human Resources & Talent Acquisition", "Balaji P"),
    ("MIS", "Sivasankari P"),
    ("Finance & Accounts", "Sahendra Kondibhau Naik"),
    ("Business Transformation", None),
]

HR = "Human Resources & Talent Acquisition"

# App users. (name, role, team, department, manager name)
USERS: list[tuple[str, Role, Team, str, str | None]] = [
    # HR / TA / PR core
    ("Balaji P", Role.HR_HEAD, Team.MGMT, HR, None),
    ("S Muthahir Ahmed", Role.TA_TL, Team.TA, HR, "Balaji P"),
    ("Pavithra S", Role.TA_RECRUITER, Team.TA, HR, "S Muthahir Ahmed"),
    ("Twinkle Amaldia Pereira", Role.TA_RECRUITER, Team.TA, HR, "S Muthahir Ahmed"),
    ("Nithyalakshmi Shivakumar", Role.TA_RECRUITER, Team.TA, HR, "S Muthahir Ahmed"),
    ("Sowmya Murugan", Role.PR, Team.PR, HR, "Balaji P"),
    ("Preetha", Role.PR, Team.PR, HR, "Balaji P"),
    ("Susita Powdel", Role.PR, Team.PR, HR, "Sowmya Murugan"),
    # Department interviewers (L4 = Team Lead, L5 = Head)
    ("MosesDevanbu Sasikumar RE", Role.DEPT_HEAD, Team.DEPT, "Transactions - Coding", None),
    (
        "Sathish Hubert U",
        Role.DEPT_LEAD,
        Team.DEPT,
        "Transactions - Coding",
        "MosesDevanbu Sasikumar RE",
    ),
    ("Prabhu V", Role.DEPT_HEAD, Team.DEPT, "Quality Assurance", None),
    ("Charles Sundarraj", Role.DEPT_HEAD, Team.DEPT, "RCM", None),
    ("Suresh Reddy K", Role.DEPT_HEAD, Team.DEPT, "Software", None),
]


def email_for(name: str) -> str:
    tokens = re.findall(r"[A-Za-z]+", name.lower())
    return ".".join(tokens) + "@" + EMAIL_DOMAIN if tokens else "unknown@" + EMAIL_DOMAIN


def _upsert_department(db: Session, name: str) -> Department:
    dept = db.scalar(select(Department).where(Department.name == name))
    if dept is None:
        dept = Department(name=name)
        db.add(dept)
        db.flush()
    return dept


def _upsert_user(db: Session, name: str, role: Role, team: Team, dept_id: int | None) -> User:
    email = email_for(name)
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(email=email, name=name, role=role, team=team, department_id=dept_id)
        db.add(user)
        db.flush()
    else:
        user.name, user.role, user.team, user.department_id = name, role, team, dept_id
    return user


def run(db: Session) -> None:
    dept_ids = {name: _upsert_department(db, name).id for name, _ in DEPARTMENTS}

    user_ids: dict[str, int] = {}
    for name, role, team, dept_name, _ in USERS:
        user = _upsert_user(db, name, role, team, dept_ids.get(dept_name))
        user_ids[name] = user.id

    # Second pass: manager links.
    for name, _, _, _, manager_name in USERS:
        if manager_name and manager_name in user_ids:
            db.get(User, user_ids[name]).manager_id = user_ids[manager_name]  # type: ignore[union-attr]

    # Department heads.
    for dept_name, head_name in DEPARTMENTS:
        if head_name and head_name in user_ids:
            dept = db.get(Department, dept_ids[dept_name])
            if dept is not None:
                dept.head_user_id = user_ids[head_name]

    db.commit()
    _seed_sample_requisitions(db, dept_ids, user_ids)


# Demo requisitions (title, department, headcount, urgency, recruiter name | None).
SAMPLE_REQS: list[tuple[str, str, int, Urgency, str | None]] = [
    ("Senior Medical Coder", "Transactions - Coding", 3, Urgency.HIGH, None),
    ("AR Caller (Night Shift)", "RCM", 5, Urgency.URGENT, None),
    ("Quality Analyst - Coding", "Quality Assurance", 2, Urgency.NORMAL, "Pavithra S"),
    ("HCC Coder", "HCC", 1, Urgency.NORMAL, "Twinkle Amaldia Pereira"),
]


def _seed_sample_requisitions(
    db: Session, dept_ids: dict[str, int], user_ids: dict[str, int]
) -> None:
    if db.scalar(select(func.count()).select_from(Requisition)):
        return  # only seed demo data into an empty table
    hr_head_id = user_ids.get("Balaji P")
    for title, dept_name, headcount, urgency, recruiter in SAMPLE_REQS:
        req = Requisition(
            code="",
            title=title,
            department_id=dept_ids[dept_name],
            headcount=headcount,
            urgency=urgency,
            status=(RequisitionStatus.ASSIGNED if recruiter else RequisitionStatus.SUBMITTED),
            created_by_id=hr_head_id,
            assigned_recruiter_id=user_ids.get(recruiter) if recruiter else None,
        )
        db.add(req)
        db.flush()
        req.code = make_code(req.id)
    db.commit()


def main() -> None:
    with SessionLocal() as db:
        run(db)
    print(f"Seeded {len(DEPARTMENTS)} departments and {len(USERS)} users.")


if __name__ == "__main__":
    main()
