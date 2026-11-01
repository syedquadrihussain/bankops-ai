from fastapi.testclient import TestClient

from app import auth
from app.main import app

anon = TestClient(app)
BODY = {"question": "identity verification", "limit": 1}


def bearer(username, role, minutes=30):
    token = auth.create_access_token(username, role, minutes=minutes)
    return {"Authorization": "Bearer " + token}


def start_research(headers):
    response = anon.post("/research", json=BODY, headers=headers)
    assert response.status_code == 200
    return response.json()


def test_research_without_token_returns_401():
    assert anon.post("/research", json=BODY).status_code == 401


def test_research_with_garbage_token_returns_401():
    headers = {"Authorization": "Bearer not-a-token"}
    assert anon.post("/research", json=BODY, headers=headers).status_code == 401


def test_research_with_expired_token_returns_401():
    headers = bearer("asha", "analyst", minutes=-1)
    assert anon.post("/research", json=BODY, headers=headers).status_code == 401


def test_review_endpoints_without_token_return_401():
    review_id = start_research(bearer("asha", "analyst"))["review_id"]
    assert anon.get(f"/reviews/{review_id}").status_code == 401
    assert anon.get(f"/reviews/{review_id}/audit").status_code == 401
    decision = anon.post(
        f"/reviews/{review_id}/decision", json={"decision": "approve"}
    )
    assert decision.status_code == 401


def test_analyst_can_research_and_read_but_cannot_decide():
    analyst = bearer("asha", "analyst")
    review_id = start_research(analyst)["review_id"]
    assert anon.get(f"/reviews/{review_id}", headers=analyst).status_code == 200
    assert anon.get(f"/reviews/{review_id}/audit", headers=analyst).status_code == 200
    decision = anon.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "approve"},
        headers=analyst,
    )
    assert decision.status_code == 403
    review = anon.get(f"/reviews/{review_id}", headers=analyst).json()
    assert review["review_status"] == "pending_review"


def test_reviewer_decision_uses_the_name_from_the_token():
    review_id = start_research(bearer("asha", "analyst"))["review_id"]
    reviewer = bearer("ravi", "reviewer")
    decision = anon.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "approve", "reviewer": "someone-else"},
        headers=reviewer,
    )
    assert decision.status_code == 200
    assert decision.json()["reviewer"] == "ravi"
    audit = anon.get(f"/reviews/{review_id}/audit", headers=reviewer).json()
    assert audit["events"][-1]["event"] == "review_approved"
    assert audit["events"][-1]["actor"] == "ravi"


def test_audit_log_records_who_started_the_research():
    analyst = bearer("asha", "analyst")
    review_id = start_research(analyst)["review_id"]
    audit = anon.get(f"/reviews/{review_id}/audit", headers=analyst).json()
    assert audit["events"][0]["event"] == "review_created"
    assert audit["events"][0]["actor"] == "asha"


def test_public_endpoints_stay_open():
    assert anon.get("/health").status_code == 200
    assert anon.get("/policies").status_code == 200
    assert anon.get("/search", params={"q": "identity"}).status_code == 200
