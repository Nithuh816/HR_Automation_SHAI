from app.models.enums import Role, Team


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


def _accepted_offer(client, hr_header, rec_header, app_id, ctc=600000):
    offer_id = client.post(
        f"/api/v1/applications/{app_id}/offers",
        headers=rec_header,
        json={"annual_ctc": ctc, "joining_date": "2026-08-01"},
    ).json()["id"]
    client.post(f"/api/v1/offers/{offer_id}/submit", headers=rec_header)
    client.post(f"/api/v1/offers/{offer_id}/approve", headers=hr_header)
    url = client.post(f"/api/v1/offers/{offer_id}/send", headers=rec_header).json()["url"]
    token = url.rsplit("/", 1)[-1]
    accepted = client.post(f"/api/v1/c/offer/{token}/accept")
    assert accepted.status_code == 200
    return offer_id


def test_queue_lists_accepted_offers_and_is_pr_only(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    pr = make_user("pr@shaihealth.com", Role.PR, Team.PR)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _accepted_offer(client, auth_header(hr.id), auth_header(rec.id), app_id)

    # A recruiter is not on the Post-Recruitment team.
    assert client.get("/api/v1/onboarding/queue", headers=auth_header(rec.id)).status_code == 403

    queue = client.get("/api/v1/onboarding/queue", headers=auth_header(pr.id))
    assert queue.status_code == 200
    rows = queue.json()
    assert len(rows) == 1
    assert rows[0]["application_id"] == app_id
    assert rows[0]["offer_status"] == "accepted"
    assert rows[0]["handoff_status"] is None  # not pushed yet


def test_push_is_idempotent_then_confirm_joining(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    pr = make_user("pr@shaihealth.com", Role.PR, Team.PR)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _accepted_offer(client, auth_header(hr.id), auth_header(rec.id), app_id)

    # A recruiter cannot push.
    assert (
        client.post(
            f"/api/v1/onboarding/applications/{app_id}/push", headers=auth_header(rec.id)
        ).status_code
        == 403
    )

    pushed = client.post(
        f"/api/v1/onboarding/applications/{app_id}/push", headers=auth_header(pr.id)
    )
    assert pushed.status_code == 200
    body = pushed.json()
    assert body["status"] == "pushed"
    assert body["greythr_employee_id"].startswith("GHR-STUB-")
    handoff_id = body["id"]

    # Idempotent: a second push returns the same handoff + employee id.
    again = client.post(
        f"/api/v1/onboarding/applications/{app_id}/push", headers=auth_header(pr.id)
    )
    assert again.status_code == 200
    assert again.json()["id"] == handoff_id
    assert again.json()["greythr_employee_id"] == body["greythr_employee_id"]

    # Confirming joining advances the application to the final pipeline stage.
    joined = client.post(
        f"/api/v1/onboarding/{handoff_id}/confirm-joining", headers=auth_header(pr.id)
    )
    assert joined.status_code == 200
    assert joined.json()["status"] == "joined"

    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["stage"] == "joined"


def test_push_requires_an_accepted_offer(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    pr = make_user("pr@shaihealth.com", Role.PR, Team.PR)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    # No offer accepted yet -> not eligible.
    assert (
        client.post(
            f"/api/v1/onboarding/applications/{app_id}/push", headers=auth_header(pr.id)
        ).status_code
        == 409
    )


def test_confirm_joining_unknown_handoff_404(client, make_user, auth_header):
    pr = make_user("pr@shaihealth.com", Role.PR, Team.PR)
    assert (
        client.post(
            "/api/v1/onboarding/999/confirm-joining", headers=auth_header(pr.id)
        ).status_code
        == 404
    )
