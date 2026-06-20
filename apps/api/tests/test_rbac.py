from app.models.enums import Role, Team


def test_hr_head_can_list_and_create_users(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    headers = auth_header(hr.id)

    listed = client.get("/api/v1/users", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    created = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "email": "New.Hire@shaihealth.com",
            "name": "New Hire",
            "role": "ta_recruiter",
            "team": "ta",
        },
    )
    assert created.status_code == 201
    assert created.json()["email"] == "new.hire@shaihealth.com"  # normalized


def test_duplicate_email_conflicts(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    headers = auth_header(hr.id)
    payload = {"email": "dup@shaihealth.com", "name": "Dup", "role": "pr", "team": "pr"}
    assert client.post("/api/v1/users", headers=headers, json=payload).status_code == 201
    assert client.post("/api/v1/users", headers=headers, json=payload).status_code == 409


def test_recruiter_forbidden_from_admin(client, make_user, auth_header):
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER)
    headers = auth_header(rec.id)
    assert client.get("/api/v1/users", headers=headers).status_code == 403
    assert client.get("/api/v1/departments", headers=headers).status_code == 403


def test_deactivate_user(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    target = make_user("temp@shaihealth.com", Role.PR, Team.PR)
    res = client.post(f"/api/v1/users/{target.id}/deactivate", headers=auth_header(hr.id))
    assert res.status_code == 200
    assert res.json()["is_active"] is False
