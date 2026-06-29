from app.models.enums import Role, Team
from app.services import notifications


def _candidate_app(client, hr_header, rec_header, dept_factory, dept_name="RCM"):
    dept = dept_factory(dept_name)
    req = client.post(
        "/api/v1/requisitions",
        headers=hr_header,
        json={"title": "Senior Coder", "department_id": dept.id, "headcount": 1},
    ).json()
    cand = client.post(
        "/api/v1/candidates",
        headers=rec_header,
        json={"name": "Asha Rao", "email": "asha@example.com", "requisition_id": req["id"]},
    ).json()
    return client.get(f"/api/v1/candidates/{cand['id']}/applications", headers=rec_header).json()[
        0
    ]["id"]


def _send_offer(client, hr_header, rec_header, app_id):
    oid = client.post(
        f"/api/v1/applications/{app_id}/offers",
        headers=rec_header,
        json={"annual_ctc": 600000, "joining_date": "2026-08-01"},
    ).json()["id"]
    client.post(f"/api/v1/offers/{oid}/submit", headers=rec_header)
    client.post(f"/api/v1/offers/{oid}/approve", headers=hr_header)
    client.post(f"/api/v1/offers/{oid}/send", headers=rec_header)


def test_sending_offer_enqueues_candidate_email(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _send_offer(client, auth_header(hr.id), auth_header(rec.id), app_id)

    outbox = client.get("/api/v1/notifications/outbox", headers=auth_header(hr.id))
    assert outbox.status_code == 200
    emails = [n for n in outbox.json() if n["kind"] == "offer_sent"]
    assert len(emails) == 1
    assert emails[0]["channel"] == "email"
    assert emails[0]["to_address"] == "asha@example.com"
    assert emails[0]["status"] == "queued"


def test_flush_delivers_outbox_hr_only(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _send_offer(client, auth_header(hr.id), auth_header(rec.id), app_id)

    # Recruiters cannot flush the outbox.
    assert (
        client.post("/api/v1/notifications/flush", headers=auth_header(rec.id)).status_code == 403
    )

    flushed = client.post("/api/v1/notifications/flush", headers=auth_header(hr.id))
    assert flushed.status_code == 200
    assert flushed.json()["delivered"] >= 1

    outbox = client.get("/api/v1/notifications/outbox", headers=auth_header(hr.id)).json()
    assert all(n["status"] == "sent" for n in outbox if n["channel"] == "email")


def test_in_app_feed_and_mark_read(client, db, make_user, auth_header):
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    notifications.in_app(db, kind="demo", recipient_user_id=rec.id, body="Hello 1")
    notifications.in_app(db, kind="demo", recipient_user_id=rec.id, body="Hello 2")
    db.commit()

    feed = client.get("/api/v1/notifications", headers=auth_header(rec.id)).json()
    assert feed["unread"] == 2
    assert len(feed["items"]) == 2

    first_id = feed["items"][0]["id"]
    read = client.post(f"/api/v1/notifications/{first_id}/read", headers=auth_header(rec.id))
    assert read.status_code == 200
    assert read.json()["read_at"] is not None

    feed2 = client.get("/api/v1/notifications", headers=auth_header(rec.id)).json()
    assert feed2["unread"] == 1


def test_enqueue_is_idempotent_on_dedupe_key(db, make_user):
    user = make_user("u@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    first = notifications.in_app(
        db, kind="sla", recipient_user_id=user.id, body="x", dedupe_key="k1"
    )
    second = notifications.in_app(
        db, kind="sla", recipient_user_id=user.id, body="x", dedupe_key="k1"
    )
    assert first is not None
    assert second is None
