from app.models.enums import Role, Team


def test_create_and_list_departments(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    headers = auth_header(hr.id)

    created = client.post(
        "/api/v1/departments", headers=headers, json={"name": "Quality Assurance"}
    )
    assert created.status_code == 201
    dept_id = created.json()["id"]

    # Assign a head that exists.
    head = make_user("head@shaihealth.com", Role.DEPT_HEAD, Team.DEPT)
    patched = client.patch(
        f"/api/v1/departments/{dept_id}", headers=headers, json={"head_user_id": head.id}
    )
    assert patched.status_code == 200
    assert patched.json()["head_user_id"] == head.id

    listed = client.get("/api/v1/departments", headers=headers)
    assert listed.status_code == 200
    assert [d["name"] for d in listed.json()] == ["Quality Assurance"]


def test_head_must_reference_existing_user(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    res = client.post(
        "/api/v1/departments",
        headers=auth_header(hr.id),
        json={"name": "RCM", "head_user_id": 9999},
    )
    assert res.status_code == 422


def test_duplicate_department_name_conflicts(client, make_user, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    headers = auth_header(hr.id)
    assert (
        client.post("/api/v1/departments", headers=headers, json={"name": "HCC"}).status_code == 201
    )
    assert (
        client.post("/api/v1/departments", headers=headers, json={"name": "HCC"}).status_code == 409
    )
