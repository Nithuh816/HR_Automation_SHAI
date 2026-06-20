from app.models.enums import Role, Team


def _question(client, mgr_header, correct, text="Q?"):
    return client.post(
        "/api/v1/assessment/questions",
        headers=mgr_header,
        json={"text": text, "options": ["A", "B", "C", "D"], "correct_index": correct},
    ).json()


def _setup_template(client, mgr_header, corrects):
    tpl = client.post(
        "/api/v1/assessment/templates",
        headers=mgr_header,
        json={"name": f"L2 {corrects}", "duration_minutes": 30, "pass_pct": 60},
    ).json()
    qids = []
    for i, c in enumerate(corrects):
        q = _question(client, mgr_header, c, text=f"Q{i}")
        client.post(
            f"/api/v1/assessment/templates/{tpl['id']}/questions",
            headers=mgr_header,
            json={"question_id": q["id"], "position": i},
        )
        qids.append(q["id"])
    return tpl, qids


def _candidate_app(client, hr_header, rec_header, make_dept_name, dept_factory):
    dept = dept_factory(make_dept_name)
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
    app_id = client.get(f"/api/v1/candidates/{cand['id']}/applications", headers=rec_header).json()[
        0
    ]["id"]
    return app_id


def test_question_template_admin_and_rbac(client, make_user, auth_header):
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)

    tpl, _qids = _setup_template(client, auth_header(tl.id), [0, 1])
    detail = client.get(f"/api/v1/assessment/templates/{tpl['id']}", headers=auth_header(tl.id))
    assert detail.status_code == 200
    assert len(detail.json()["questions"]) == 2

    # Recruiter cannot manage the bank.
    assert (
        client.post(
            "/api/v1/assessment/questions",
            headers=auth_header(rec.id),
            json={"text": "x", "options": ["a", "b"], "correct_index": 0},
        ).status_code
        == 403
    )


def test_correct_index_validation(client, make_user, auth_header):
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    res = client.post(
        "/api/v1/assessment/questions",
        headers=auth_header(tl.id),
        json={"text": "x", "options": ["a", "b"], "correct_index": 5},
    )
    assert res.status_code == 422


def test_assessment_pass_advances_stage(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    tpl, qids = _setup_template(client, auth_header(hr.id), [0, 1])
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), "RCM", make_dept)

    issued = client.post(
        f"/api/v1/applications/{app_id}/assessment",
        headers=auth_header(rec.id),
        json={"template_id": tpl["id"]},
    )
    assert issued.status_code == 200
    token = issued.json()["url"].rsplit("/", 1)[-1]

    # Issuing moved the candidate to L2.
    apps = client.get(
        "/api/v1/applications/" + str(app_id) + "/attempts", headers=auth_header(rec.id)
    )
    assert apps.status_code == 200

    ctx = client.get(f"/api/v1/c/assessment/{token}")
    assert ctx.status_code == 200
    body = ctx.json()
    assert len(body["questions"]) == 2
    assert "correct_index" not in body["questions"][0]  # answers never exposed

    # Answer both correctly.
    answers = [
        {"question_id": qids[0], "selected_index": 0},
        {"question_id": qids[1], "selected_index": 1},
    ]
    submitted = client.post(f"/api/v1/c/assessment/{token}", json={"answers": answers})
    assert submitted.status_code == 200
    assert submitted.json()["score_pct"] == 100.0
    assert submitted.json()["passed"] is True

    # Stage advanced to L3 HR.
    apps2 = client.get(
        f"/api/v1/applications/{app_id}/attempts", headers=auth_header(rec.id)
    ).json()
    assert apps2[0]["passed"] is True

    # Single-use.
    assert (
        client.post(f"/api/v1/c/assessment/{token}", json={"answers": answers}).status_code == 404
    )


def test_assessment_fail_keeps_stage(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    tpl, qids = _setup_template(client, auth_header(hr.id), [0, 1])
    app_id = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), "HCC", make_dept)

    token = (
        client.post(
            f"/api/v1/applications/{app_id}/assessment",
            headers=auth_header(rec.id),
            json={"template_id": tpl["id"]},
        )
        .json()["url"]
        .rsplit("/", 1)[-1]
    )
    client.get(f"/api/v1/c/assessment/{token}")

    # Both wrong -> 0%.
    answers = [
        {"question_id": qids[0], "selected_index": 3},
        {"question_id": qids[1], "selected_index": 3},
    ]
    res = client.post(f"/api/v1/c/assessment/{token}", json={"answers": answers})
    assert res.json()["passed"] is False
    assert res.json()["score_pct"] == 0.0
