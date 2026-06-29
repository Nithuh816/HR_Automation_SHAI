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


def test_reports_are_management_only(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    assert client.get("/api/v1/reports/summary", headers=auth_header(rec.id)).status_code == 403

    s = client.get("/api/v1/reports/summary", headers=auth_header(hr.id))
    assert s.status_code == 200
    assert s.json()["total_candidates"] == 1
    assert s.json()["active_applications"] == 1
    assert client.get("/api/v1/reports/summary", headers=auth_header(tl.id)).status_code == 200


def test_funnel_and_sources(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    funnel = client.get("/api/v1/reports/funnel", headers=auth_header(hr.id)).json()
    assert len(funnel["stages"]) == 9
    sourced = next(s for s in funnel["stages"] if s["stage"] == "sourced")
    assert sourced["count"] == 1  # the one application reached "sourced"
    joined = next(s for s in funnel["stages"] if s["stage"] == "joined")
    assert joined["count"] == 0

    sources = client.get("/api/v1/reports/sources", headers=auth_header(hr.id)).json()
    assert sum(s["count"] for s in sources) == 1


def test_recruiter_performance(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA, name="Asha Recruiter")
    _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    perf = client.get("/api/v1/reports/recruiter-performance", headers=auth_header(hr.id)).json()
    row = next(r for r in perf if r["recruiter_id"] == rec.id)
    assert row["candidates"] == 1
    assert row["hires"] == 0
