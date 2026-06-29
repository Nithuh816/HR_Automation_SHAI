from datetime import UTC, datetime, timedelta

from app.models.candidate import Candidate, CandidateApplication
from app.models.enums import ApplicationStatus, Role, Team
from app.services import consent as consent_svc
from app.services import retention


def _candidate(client, hr_header, rec_header, make_dept):
    dept = make_dept("RCM")
    req = client.post(
        "/api/v1/requisitions",
        headers=hr_header,
        json={"title": "Coder", "department_id": dept.id, "headcount": 1},
    ).json()
    cand = client.post(
        "/api/v1/candidates",
        headers=rec_header,
        json={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "phone": "+919900112233",
            "requisition_id": req["id"],
        },
    ).json()
    app_id = client.get(f"/api/v1/candidates/{cand['id']}/applications", headers=rec_header).json()[
        0
    ]["id"]
    return cand, app_id


def test_consent_record_dedupe_and_endpoint(client, db, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cand, app_id = _candidate(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    assert (
        consent_svc.record(db, application_id=app_id, purpose="documents", text="I consent")
        is not None
    )
    # Idempotent per (application, purpose).
    assert (
        consent_svc.record(db, application_id=app_id, purpose="documents", text="I consent") is None
    )
    db.commit()

    res = client.get(f"/api/v1/candidates/{cand['id']}/consents", headers=auth_header(rec.id))
    assert res.status_code == 200
    body = res.json()
    assert len(body) == 1
    assert body[0]["purpose"] == "documents"
    assert body[0]["given_at"] is not None


def test_retention_purges_old_rejected_pii(client, db, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cand, app_id = _candidate(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    app = db.get(CandidateApplication, app_id)
    app.status = ApplicationStatus.REJECTED
    app.rejection_stage = app.stage
    db.commit()

    now = datetime.now(UTC)
    # Inside the retention window -> nothing purged.
    assert retention.purge_rejected(db, now=now, retention_days=365) == 0
    # Past the window -> purged and anonymised.
    assert retention.purge_rejected(db, now=now + timedelta(days=400), retention_days=365) == 1
    candidate = db.get(Candidate, cand["id"])
    assert candidate.name == "Redacted Candidate"
    assert candidate.email != "asha@example.com"
    assert candidate.phone is None
    assert candidate.redacted_at is not None
    # Idempotent — already redacted candidates are skipped.
    assert retention.purge_rejected(db, now=now + timedelta(days=500), retention_days=365) == 0


def test_retention_spares_active_candidates(client, db, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cand, _ = _candidate(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    # The application is ACTIVE, so it's never purged — even far in the future.
    assert (
        retention.purge_rejected(
            db, now=datetime.now(UTC) + timedelta(days=5000), retention_days=365
        )
        == 0
    )
    assert db.get(Candidate, cand["id"]).name == "Asha Rao"
