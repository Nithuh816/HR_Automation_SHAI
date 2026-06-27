from app.models.enums import Role, Team


def _candidate_app(client, hr_header, rec_header, dept_factory, dept_name="RCM"):
    dept = dept_factory(dept_name)
    req = client.post(
        "/api/v1/requisitions",
        headers=hr_header,
        json={"title": "Coder", "department_id": dept.id, "headcount": 1},
    ).json()
    cand = client.post(
        "/api/v1/candidates",
        headers=rec_header,
        json={"name": "Asha Rao", "email": "asha@example.com", "requisition_id": req["id"]},
    ).json()
    return client.get(
        f"/api/v1/candidates/{cand['id']}/applications", headers=rec_header
    ).json()[0]["id"]


def _make_rubric(client, mgr_header):
    rubric = client.post(
        "/api/v1/rubrics",
        headers=mgr_header,
        json={"name": "L4 Tech", "round": "l4_tech1"},
    ).json()
    client.post(
        f"/api/v1/rubrics/{rubric['id']}/criteria",
        headers=mgr_header,
        json={"label": "Accuracy", "weight": 3, "max_score": 5},
    )
    client.post(
        f"/api/v1/rubrics/{rubric['id']}/criteria",
        headers=mgr_header,
        json={"label": "Speed", "weight": 1, "max_score": 5},
    )
    return rubric


def test_rubric_admin_and_rbac(client, make_user, auth_header):
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)

    rubric = _make_rubric(client, auth_header(tl.id))
    detail = client.get(f"/api/v1/rubrics/{rubric['id']}", headers=auth_header(tl.id))
    assert detail.status_code == 200
    assert len(detail.json()["criteria"]) == 2

    # Recruiters cannot manage rubrics.
    assert (
        client.post(
            "/api/v1/rubrics",
            headers=auth_header(rec.id),
            json={"name": "x", "round": "l3_hr"},
        ).status_code
        == 403
    )


def test_schedule_creates_teams_stub_and_moves_stage(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    lead = make_user("lead@shaihealth.com", Role.DEPT_LEAD, Team.DEPT)
    rubric = _make_rubric(client, auth_header(hr.id))
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    res = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header(rec.id),
        json={
            "round": "l4_tech1",
            "mode": "online",
            "scheduled_at": "2026-07-01T10:00:00Z",
            "duration_minutes": 45,
            "interviewer_id": lead.id,
            "rubric_template_id": rubric["id"],
        },
    )
    assert res.status_code == 201
    body = res.json()
    assert body["teams_join_url"].startswith("https://teams.microsoft.com/")
    assert body["interviewer_name"] == lead.name

    # Application advanced to the round's stage.
    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["stage"] == "l4_tech1"


def test_in_person_interview_has_no_teams_url(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    res = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header(rec.id),
        json={
            "round": "l3_hr",
            "mode": "in_person",
            "scheduled_at": "2026-07-01T10:00:00Z",
            "interviewer_id": hr.id,
            "location": "Chennai HO, Room 2",
        },
    )
    assert res.status_code == 201
    assert res.json()["teams_join_url"] is None
    assert res.json()["location"] == "Chennai HO, Room 2"


def test_scorecard_pass_advances_and_only_interviewer(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    lead = make_user("lead@shaihealth.com", Role.DEPT_LEAD, Team.DEPT)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    interview = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header(rec.id),
        json={
            "round": "l4_tech1",
            "mode": "online",
            "scheduled_at": "2026-07-01T10:00:00Z",
            "interviewer_id": lead.id,
        },
    ).json()

    payload = {
        "decision": "yes",
        "strengths": "Strong on CPT.",
        "scores": [
            {"label": "Accuracy", "score": 4, "weight": 3},
            {"label": "Speed", "score": 3, "weight": 1},
        ],
    }

    # A recruiter who is not the interviewer cannot submit.
    assert (
        client.post(
            f"/api/v1/interviews/{interview['id']}/scorecard",
            headers=auth_header(rec.id),
            json=payload,
        ).status_code
        == 403
    )

    # The assigned interviewer can.
    res = client.post(
        f"/api/v1/interviews/{interview['id']}/scorecard",
        headers=auth_header(lead.id),
        json=payload,
    )
    assert res.status_code == 200
    assert res.json()["status"] == "completed"
    assert res.json()["scorecard"]["overall_score"] == 3.75  # (4*3 + 3*1) / 4

    # Passing L4 advanced the candidate to L5.
    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["stage"] == "l5_tech2"

    # Single scorecard per interview.
    assert (
        client.post(
            f"/api/v1/interviews/{interview['id']}/scorecard",
            headers=auth_header(lead.id),
            json=payload,
        ).status_code
        == 409
    )


def test_scorecard_reject_ends_application(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    interview = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header(rec.id),
        json={
            "round": "l3_hr",
            "mode": "phone",
            "scheduled_at": "2026-07-01T10:00:00Z",
            "interviewer_id": hr.id,
        },
    ).json()

    res = client.post(
        f"/api/v1/interviews/{interview['id']}/scorecard",
        headers=auth_header(hr.id),
        json={"decision": "strong_no", "concerns": "Not eligible.", "scores": []},
    )
    assert res.status_code == 200

    app = client.get("/api/v1/candidates/1/applications", headers=auth_header(rec.id)).json()[0]
    assert app["status"] == "rejected"
    assert app["rejection_stage"] == "l3_hr"


def test_reschedule_and_cancel(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)

    interview = client.post(
        f"/api/v1/applications/{app_id}/interviews",
        headers=auth_header(rec.id),
        json={
            "round": "l4_tech1",
            "mode": "online",
            "scheduled_at": "2026-07-01T10:00:00Z",
            "interviewer_id": hr.id,
        },
    ).json()

    re = client.post(
        f"/api/v1/interviews/{interview['id']}/reschedule",
        headers=auth_header(rec.id),
        json={"scheduled_at": "2026-07-02T14:00:00Z"},
    )
    assert re.status_code == 200
    assert re.json()["status"] == "rescheduled"

    cancel = client.post(
        f"/api/v1/interviews/{interview['id']}/cancel", headers=auth_header(rec.id)
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"

    # Today's board excludes the cancelled interview.
    today = client.get("/api/v1/interviews/today", headers=auth_header(hr.id))
    assert today.status_code == 200
    assert all(i["id"] != interview["id"] for i in today.json())
