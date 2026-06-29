from app.models.enums import Role, Team


def test_audit_records_actions_and_is_hr_only(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    dept = make_dept("RCM")

    created = client.post(
        "/api/v1/requisitions",
        headers=auth_header(hr.id),
        json={"title": "Coder", "department_id": dept.id, "headcount": 1},
    )
    assert created.status_code == 201
    req_id = created.json()["id"]
    client.post(
        f"/api/v1/requisitions/{req_id}/assign",
        headers=auth_header(hr.id),
        json={"recruiter_id": rec.id},
    )

    # The audit log is HR-Head-only.
    assert client.get("/api/v1/audit-log", headers=auth_header(rec.id)).status_code == 403

    log = client.get("/api/v1/audit-log", headers=auth_header(hr.id))
    assert log.status_code == 200
    entries = log.json()
    actions = [e["action"] for e in entries]
    assert "requisition.created" in actions
    assert "requisition.assigned" in actions

    entry = next(e for e in entries if e["action"] == "requisition.created")
    assert entry["actor_user_id"] == hr.id
    assert entry["entity_type"] == "requisition"
    assert entry["entity_id"] == req_id


def test_audit_filter_by_entity_type(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    dept = make_dept("RCM")
    client.post(
        "/api/v1/requisitions",
        headers=auth_header(hr.id),
        json={"title": "Coder", "department_id": dept.id, "headcount": 1},
    )

    offers = client.get("/api/v1/audit-log?entity_type=offer", headers=auth_header(hr.id))
    assert offers.status_code == 200
    assert all(e["entity_type"] == "offer" for e in offers.json())

    reqs = client.get("/api/v1/audit-log?entity_type=requisition", headers=auth_header(hr.id))
    assert len(reqs.json()) >= 1
    assert all(e["entity_type"] == "requisition" for e in reqs.json())
