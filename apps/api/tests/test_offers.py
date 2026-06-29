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


def _draft_offer(client, rec_header, app_id, ctc=600000):
    return client.post(
        f"/api/v1/applications/{app_id}/offers",
        headers=rec_header,
        json={"annual_ctc": ctc, "joining_date": "2026-08-01"},
    )


def test_create_computes_breakdown_and_moves_stage(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    res = _draft_offer(client, auth_header(rec.id), app_id, ctc=1000000)
    assert res.status_code == 201
    body = res.json()
    assert body["designation"] == "Senior Coder"  # defaulted from requisition
    # Components sum back to the CTC (the "Total CTC" row equals annual_ctc).
    total = next(c for c in body["components"] if c["label"] == "Total CTC")
    assert total["annual"] == 1000000
    earning_rows = [c for c in body["components"] if c["label"] != "Total CTC"]
    assert sum(c["annual"] for c in earning_rows) == 1000000

    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["stage"] == "offer"


def test_approval_flow_and_rbac(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    offer_id = _draft_offer(client, auth_header(rec.id), app_id).json()["id"]

    # Cannot send before approval.
    assert (
        client.post(f"/api/v1/offers/{offer_id}/send", headers=auth_header(rec.id)).status_code
        == 409
    )

    client.post(f"/api/v1/offers/{offer_id}/submit", headers=auth_header(rec.id))
    # A recruiter cannot approve.
    assert (
        client.post(f"/api/v1/offers/{offer_id}/approve", headers=auth_header(rec.id)).status_code
        == 403
    )
    approved = client.post(f"/api/v1/offers/{offer_id}/approve", headers=auth_header(hr.id))
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_by_id"] == hr.id

    sent = client.post(f"/api/v1/offers/{offer_id}/send", headers=auth_header(rec.id))
    assert sent.status_code == 200
    assert sent.json()["offer"]["status"] == "sent"
    assert "/offer/" in sent.json()["url"]


def test_edit_only_in_draft(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    offer_id = _draft_offer(client, auth_header(rec.id), app_id, ctc=500000).json()["id"]

    patched = client.patch(
        f"/api/v1/offers/{offer_id}",
        headers=auth_header(rec.id),
        json={"annual_ctc": 800000},
    )
    assert patched.status_code == 200
    total = next(c for c in patched.json()["components"] if c["label"] == "Total CTC")
    assert total["annual"] == 800000

    client.post(f"/api/v1/offers/{offer_id}/submit", headers=auth_header(rec.id))
    # No longer a draft -> editing is rejected.
    assert (
        client.patch(
            f"/api/v1/offers/{offer_id}", headers=auth_header(rec.id), json={"annual_ctc": 900000}
        ).status_code
        == 409
    )


def _send(client, hr_header, rec_header, app_id):
    offer_id = _draft_offer(client, rec_header, app_id).json()["id"]
    client.post(f"/api/v1/offers/{offer_id}/submit", headers=rec_header)
    client.post(f"/api/v1/offers/{offer_id}/approve", headers=hr_header)
    url = client.post(f"/api/v1/offers/{offer_id}/send", headers=rec_header).json()["url"]
    return offer_id, url.rsplit("/", 1)[-1]


def test_candidate_accepts_offer(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _offer_id, token = _send(client, auth_header(hr.id), auth_header(rec.id), app_id)

    ctx = client.get(f"/api/v1/c/offer/{token}")
    assert ctx.status_code == 200
    assert ctx.json()["status"] == "sent"
    assert "Senior Coder" in ctx.json()["letter_html"]

    accepted = client.post(f"/api/v1/c/offer/{token}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

    # Single-use: the link is now burned.
    assert client.post(f"/api/v1/c/offer/{token}/accept").status_code == 404


def test_candidate_declines_offer_rejects_application(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    _offer_id, token = _send(client, auth_header(hr.id), auth_header(rec.id), app_id)

    declined = client.post(
        f"/api/v1/c/offer/{token}/decline", json={"reason": "Accepted another offer"}
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["status"] == "rejected"


def test_offer_template_admin_rbac(client, make_user, auth_header):
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)

    created = client.post(
        "/api/v1/offer-templates",
        headers=auth_header(tl.id),
        json={"name": "Std", "subject": "Offer", "body_md": "Hi {{ candidate_name }}"},
    )
    assert created.status_code == 201

    # Recruiters cannot manage offer templates.
    assert (
        client.post(
            "/api/v1/offer-templates",
            headers=auth_header(rec.id),
            json={"name": "x", "subject": "y", "body_md": "z"},
        ).status_code
        == 403
    )
