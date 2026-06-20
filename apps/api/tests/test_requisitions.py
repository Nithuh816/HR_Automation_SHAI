from app.models.enums import Role, Team


def _req_payload(dept_id: int, **over):
    base = {"title": "Senior Medical Coder", "department_id": dept_id, "headcount": 2}
    base.update(over)
    return base


def test_create_assign_and_inbox_flow(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    recruiter = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("Transactions - Coding")
    hr_h = auth_header(hr.id)

    # Create -> lands in triage (SUBMITTED) with an auto code.
    created = client.post("/api/v1/requisitions", headers=hr_h, json=_req_payload(dept.id))
    assert created.status_code == 201
    req = created.json()
    assert req["status"] == "submitted"
    assert req["code"].startswith("REQ-")

    # Triage inbox shows it.
    inbox = client.get("/api/v1/requisitions/inbox", headers=hr_h)
    assert inbox.status_code == 200
    assert [r["id"] for r in inbox.json()] == [req["id"]]

    # Assign to the recruiter -> ASSIGNED, leaves the inbox.
    assigned = client.post(
        f"/api/v1/requisitions/{req['id']}/assign",
        headers=hr_h,
        json={"recruiter_id": recruiter.id},
    )
    assert assigned.status_code == 200
    assert assigned.json()["status"] == "assigned"
    assert assigned.json()["assigned_recruiter_id"] == recruiter.id
    assert client.get("/api/v1/requisitions/inbox", headers=hr_h).json() == []


def test_recruiter_cannot_create_and_sees_only_assigned(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    r1 = make_user("r1@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    r2 = make_user("r2@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("RCM")

    # Recruiter cannot raise a requisition.
    assert (
        client.post(
            "/api/v1/requisitions", headers=auth_header(r1.id), json=_req_payload(dept.id)
        ).status_code
        == 403
    )

    # HR creates two, assigns one to r1.
    a = client.post(
        "/api/v1/requisitions", headers=auth_header(hr.id), json=_req_payload(dept.id)
    ).json()
    client.post("/api/v1/requisitions", headers=auth_header(hr.id), json=_req_payload(dept.id))
    client.post(
        f"/api/v1/requisitions/{a['id']}/assign",
        headers=auth_header(hr.id),
        json={"recruiter_id": r1.id},
    )

    # r1 sees only their assigned one; r2 sees none.
    r1_list = client.get("/api/v1/requisitions", headers=auth_header(r1.id)).json()
    assert [r["id"] for r in r1_list] == [a["id"]]
    assert client.get("/api/v1/requisitions", headers=auth_header(r2.id)).json() == []


def test_status_transitions(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    dept = make_dept("Quality Assurance")
    hr_h = auth_header(hr.id)
    req = client.post("/api/v1/requisitions", headers=hr_h, json=_req_payload(dept.id)).json()

    # SUBMITTED -> FILLED is illegal.
    bad = client.post(
        f"/api/v1/requisitions/{req['id']}/status", headers=hr_h, json={"status": "filled"}
    )
    assert bad.status_code == 409

    # SUBMITTED -> ON_HOLD -> CANCELLED is legal.
    ok = client.post(
        f"/api/v1/requisitions/{req['id']}/status", headers=hr_h, json={"status": "on_hold"}
    )
    assert ok.status_code == 200 and ok.json()["status"] == "on_hold"
    ok2 = client.post(
        f"/api/v1/requisitions/{req['id']}/status", headers=hr_h, json={"status": "cancelled"}
    )
    assert ok2.status_code == 200 and ok2.json()["status"] == "cancelled"


def test_comments_and_summary(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("HCC")
    hr_h = auth_header(hr.id)

    r = client.post(
        "/api/v1/requisitions", headers=hr_h, json=_req_payload(dept.id, headcount=3)
    ).json()
    client.post(
        f"/api/v1/requisitions/{r['id']}/assign", headers=hr_h, json={"recruiter_id": rec.id}
    )

    # Comment.
    c = client.post(
        f"/api/v1/requisitions/{r['id']}/comments", headers=hr_h, json={"body": "Priority hire"}
    )
    assert c.status_code == 201
    assert (
        client.get(f"/api/v1/requisitions/{r['id']}/comments", headers=hr_h).json()[0]["body"]
        == "Priority hire"
    )

    # Summary reflects the assigned requisition + its headcount.
    summary = client.get("/api/v1/dashboard/requisitions", headers=hr_h).json()
    assert summary["total"] == 1
    assert summary["assigned"] == 1
    assert summary["open_headcount"] == 3
    assert summary["by_urgency"]["normal"] == 1
