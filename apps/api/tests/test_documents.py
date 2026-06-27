import io

from app.models.enums import Role, Team


def _candidate_app(client, hr_header, rec_header, dept_factory, fresher=False):
    dept = dept_factory("RCM")
    req = client.post(
        "/api/v1/requisitions",
        headers=hr_header,
        json={"title": "Coder", "department_id": dept.id, "headcount": 1},
    ).json()
    cand = client.post(
        "/api/v1/candidates",
        headers=rec_header,
        json={
            "name": "Asha Rao",
            "email": "asha@example.com",
            "is_fresher": fresher,
            "requisition_id": req["id"],
        },
    ).json()
    return cand["id"]


def _upload_token(client, rec_header, candidate_id):
    url = client.post(
        f"/api/v1/candidates/{candidate_id}/upload-link", headers=rec_header
    ).json()["url"]
    return url.rsplit("/", 1)[-1]


def _post_file(client, token, doc_type, content, filename="doc.txt", ctype="text/plain"):
    return client.post(
        f"/api/v1/c/upload/{token}",
        data={"document_type": doc_type, "consent": "true"},
        files={"file": (filename, io.BytesIO(content), ctype)},
    )


def test_checklist_admin_and_rbac(client, make_user, auth_header):
    tl = make_user("tl@shaihealth.com", Role.TA_TL, Team.TA)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)

    created = client.post(
        "/api/v1/checklists",
        headers=auth_header(tl.id),
        json={"checklist_type": "fresher", "document_type": "pan", "label": "PAN"},
    )
    assert created.status_code == 201

    # Recruiters cannot manage checklists.
    assert (
        client.post(
            "/api/v1/checklists",
            headers=auth_header(rec.id),
            json={"checklist_type": "fresher", "document_type": "pan", "label": "x"},
        ).status_code
        == 403
    )


def test_upload_extracts_pan_and_encrypts(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cid = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    token = _upload_token(client, auth_header(rec.id), cid)

    res = _post_file(client, token, "pan", b"My PAN is ABCDE1234F, please verify.")
    assert res.status_code == 200
    uploaded = res.json()["uploaded"]
    assert len(uploaded) == 1
    assert uploaded[0]["status"] == "extracted"

    # Recruiter sees the doc with a MASKED pan — never the raw number.
    docs = client.get(f"/api/v1/candidates/{cid}/documents", headers=auth_header(rec.id)).json()
    assert docs[0]["pan_masked"].endswith("234F")
    assert "ABCDE1234F" not in (docs[0]["pan_masked"] or "")
    assert "aadhaar" not in str(docs[0]).lower() or docs[0]["aadhaar_masked"] is None


def test_unreadable_image_goes_to_review(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cid = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    token = _upload_token(client, auth_header(rec.id), cid)

    # A binary image with no OCR available -> manual review.
    res = _post_file(client, token, "aadhaar", b"\x89PNG\r\n\x1a\n\x00", "id.png", "image/png")
    assert res.status_code == 200
    assert res.json()["uploaded"][0]["status"] == "needs_review"


def test_consent_required(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cid = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    token = _upload_token(client, auth_header(rec.id), cid)

    res = client.post(
        f"/api/v1/c/upload/{token}",
        data={"document_type": "pan", "consent": "false"},
        files={"file": ("doc.txt", io.BytesIO(b"ABCDE1234F"), "text/plain")},
    )
    assert res.status_code == 422


def test_verify_and_fetch_file(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    cid = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept)
    token = _upload_token(client, auth_header(rec.id), cid)
    _post_file(client, token, "resume", b"Asha Rao - resume text", "cv.txt")

    doc_id = client.get(
        f"/api/v1/candidates/{cid}/documents", headers=auth_header(rec.id)
    ).json()[0]["id"]

    # The raw file is served behind auth, never in the JSON list.
    f = client.get(f"/api/v1/documents/{doc_id}/file", headers=auth_header(rec.id))
    assert f.status_code == 200
    assert b"resume text" in f.content

    verified = client.post(f"/api/v1/documents/{doc_id}/verify", headers=auth_header(hr.id))
    assert verified.status_code == 200
    assert verified.json()["status"] == "verified"
    assert verified.json()["reviewed_by_id"] == hr.id


def test_upload_link_requires_active_application(client, make_user, auth_header):
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    # Candidate with no application.
    cand = client.post(
        "/api/v1/candidates",
        headers=auth_header(rec.id),
        json={"name": "No App", "email": "noapp@example.com"},
    ).json()
    res = client.post(f"/api/v1/candidates/{cand['id']}/upload-link", headers=auth_header(rec.id))
    assert res.status_code == 409


def test_upload_portal_lists_checklist(client, make_user, make_dept, auth_header):
    hr = make_user("boss@shaihealth.com", Role.HR_HEAD, Team.MGMT)
    rec = make_user("rec@shaihealth.com", Role.TA_RECRUITER, Team.TA)
    # Seed two checklist items for experienced candidates.
    for dt, label in (("aadhaar", "Aadhaar"), ("relieving_letter", "Relieving letter")):
        client.post(
            "/api/v1/checklists",
            headers=auth_header(hr.id),
            json={"checklist_type": "experienced", "document_type": dt, "label": label},
        )
    cid = _candidate_app(client, auth_header(hr.id), auth_header(rec.id), make_dept, fresher=False)
    token = _upload_token(client, auth_header(rec.id), cid)

    ctx = client.get(f"/api/v1/c/upload/{token}")
    assert ctx.status_code == 200
    assert ctx.json()["checklist_type"] == "experienced"
    assert len(ctx.json()["items"]) == 2
    assert "consent" in ctx.json()["consent_text"].lower()
