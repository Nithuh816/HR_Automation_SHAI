from app.models.enums import Role, Team


def test_dev_login_and_me(client, make_user):
    user = make_user("hr.head@shaihealth.com", Role.HR_HEAD, Team.MGMT, "HR Head")

    res = client.post("/api/v1/auth/dev-login", json={"email": user.email})
    assert res.status_code == 200
    token = res.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["email"] == user.email
    assert body["role"] == "hr_head"
    assert "ms_oid" not in body  # never exposed


def test_dev_login_unknown_user(client, db_tables):
    res = client.post("/api/v1/auth/dev-login", json={"email": "nobody@shaihealth.com"})
    assert res.status_code == 401


def test_dev_login_inactive_user(client, make_user, db):
    user = make_user("gone@shaihealth.com", Role.TA_RECRUITER)
    user.is_active = False
    db.commit()
    res = client.post("/api/v1/auth/dev-login", json={"email": user.email})
    assert res.status_code == 401


def test_me_requires_auth(client, db_tables):
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401
