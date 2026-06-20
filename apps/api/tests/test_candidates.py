from app.models.enums import Role, Team


def _make_req(client, hr_header, dept_id):
    return client.post(
        "/api/v1/requisitions",
        headers=hr_header,
        json={"title": "Medical Coder", "department_id": dept_id, "headcount": 2},
    ).json()


def _candidate_payload(**over):
    base = {"name": "Asha Rao", "email": "asha@example.com", "source": "linkedin"}
    base.update(over)
    return base


def test_create_candidate_with_application_and_board(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("Transactions - Coding")
    req = _make_req(client, auth_header(hr.id), dept.id)

    created = client.post(
        "/api/v1/candidates",
        headers=auth_header(rec.id),
        json=_candidate_payload(requisition_id=req["id"]),
    )
    assert created.status_code == 201
    cand = created.json()
    assert cand["email"] == "asha@example.com"

    board = client.get(f"/api/v1/pipeline/{req['id']}", headers=auth_header(rec.id))
    assert board.status_code == 200
    cards = board.json()
    assert len(cards) == 1
    assert cards[0]["candidate_name"] == "Asha Rao"
    assert cards[0]["stage"] == "sourced"


def test_dept_head_cannot_create_candidate(client, make_user, auth_header):
    dh = make_user("dh@shaihealth.com", Role.DEPT_HEAD, Team.DEPT)
    res = client.post("/api/v1/candidates", headers=auth_header(dh.id), json=_candidate_payload())
    assert res.status_code == 403


def test_stage_move_and_reject(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("RCM")
    req = _make_req(client, auth_header(hr.id), dept.id)
    cand = client.post(
        "/api/v1/candidates",
        headers=auth_header(rec.id),
        json=_candidate_payload(requisition_id=req["id"]),
    ).json()
    app_id = client.get(
        f"/api/v1/candidates/{cand['id']}/applications", headers=auth_header(rec.id)
    ).json()[0]["id"]

    moved = client.post(
        f"/api/v1/applications/{app_id}/stage",
        headers=auth_header(rec.id),
        json={"stage": "l3_hr"},
    )
    assert moved.status_code == 200 and moved.json()["stage"] == "l3_hr"

    rejected = client.post(
        f"/api/v1/applications/{app_id}/reject",
        headers=auth_header(rec.id),
        json={"reason": "Notice period too long"},
    )
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["status"] == "rejected"
    assert body["rejection_stage"] == "l3_hr"

    # No further moves once rejected.
    again = client.post(
        f"/api/v1/applications/{app_id}/stage",
        headers=auth_header(rec.id),
        json={"stage": "l4_tech1"},
    )
    assert again.status_code == 409


def test_l1_magic_link_flow(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("HCC")
    req = _make_req(client, auth_header(hr.id), dept.id)
    cand = client.post(
        "/api/v1/candidates",
        headers=auth_header(rec.id),
        json=_candidate_payload(requisition_id=req["id"]),
    ).json()
    app_id = client.get(
        f"/api/v1/candidates/{cand['id']}/applications", headers=auth_header(rec.id)
    ).json()[0]["id"]

    link = client.post(f"/api/v1/applications/{app_id}/l1-link", headers=auth_header(rec.id))
    assert link.status_code == 200
    token = link.json()["url"].rsplit("/", 1)[-1]

    # Candidate opens the form (no auth header).
    ctx = client.get(f"/api/v1/c/l1/{token}")
    assert ctx.status_code == 200
    assert ctx.json()["candidate_name"] == "Asha Rao"
    assert ctx.json()["already_submitted"] is False

    # Candidate submits.
    submitted = client.post(
        f"/api/v1/c/l1/{token}",
        json={"payload": {"father_name": "Rao", "willing_to_relocate": True}},
    )
    assert submitted.status_code == 200
    assert submitted.json()["already_submitted"] is True

    # Stage advanced to L1.
    apps = client.get(
        f"/api/v1/candidates/{cand['id']}/applications", headers=auth_header(rec.id)
    ).json()
    assert apps[0]["stage"] == "l1_application"

    # Link is single-use now.
    assert client.get(f"/api/v1/c/l1/{token}").status_code == 404
    assert client.get("/api/v1/c/l1/not-a-real-token").status_code == 404
