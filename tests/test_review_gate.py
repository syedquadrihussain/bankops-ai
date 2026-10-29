import pytest
from fastapi.testclient import TestClient

from app.main import app, review_lock, review_records
from app.research_graph import research_graph


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_demo_review_records():
    with review_lock:
        review_records.clear()
    yield
    with review_lock:
        review_records.clear()


def create_pending_review():
    response = client.post(
        "/research",
        json={"question": "identity verification", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "pending_review"
    assert body["review_id"]
    return body


def test_verified_research_is_pending_human_review():
    result = research_graph.invoke({
        "question": "identity verification",
        "limit": 5,
    })
    assert result["verification_status"] == "passed"
    assert result["review_status"] == "pending_review"
    assert result["results"]


def test_no_matches_do_not_require_review():
    result = research_graph.invoke({
        "question": "zzznomatchingpolicyterm",
        "limit": 5,
    })
    assert result["status"] == "no_matching_policies"
    assert result["review_status"] == "not_required"


def test_research_api_returns_pending_review_status():
    body = create_pending_review()
    assert body["verification_status"] == "passed"
    assert "awaiting human review" in body["message"]


def test_research_api_does_not_require_review_when_no_matches():
    response = client.post(
        "/research",
        json={"question": "zzznomatchingpolicyterm", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "no_matching_policies"
    assert body["review_status"] == "not_required"
    assert body["count"] == 0
    assert "review_id" not in body


def test_review_can_be_approved():
    pending = create_pending_review()
    response = client.post(
        f"/reviews/{pending['review_id']}/decision",
        json={"decision": "approve", "reviewer": "reviewer-demo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "approved"
    assert body["decision"] == "approve"
    assert body["reviewer"] == "reviewer-demo"
    assert body["decided_at"]
    assert "No banking action was executed" in body["message"]


def test_review_can_be_rejected():
    pending = create_pending_review()
    response = client.post(
        f"/reviews/{pending['review_id']}/decision",
        json={"decision": "reject", "reviewer": "reviewer-demo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["review_status"] == "rejected"
    assert body["decision"] == "reject"
    assert body["decided_at"]


def test_unknown_review_id_returns_404():
    response = client.post(
        "/reviews/not-a-real-review/decision",
        json={"decision": "approve", "reviewer": "reviewer-demo"},
    )
    assert response.status_code == 404


def test_invalid_decision_returns_422():
    pending = create_pending_review()
    response = client.post(
        f"/reviews/{pending['review_id']}/decision",
        json={"decision": "maybe", "reviewer": "reviewer-demo"},
    )
    assert response.status_code == 422

    review = client.get(f"/reviews/{pending['review_id']}")
    assert review.json()["review_status"] == "pending_review"


def test_blank_reviewer_returns_422():
    pending = create_pending_review()
    response = client.post(
        f"/reviews/{pending['review_id']}/decision",
        json={"decision": "approve", "reviewer": "   "},
    )
    assert response.status_code == 422


def test_review_cannot_be_decided_twice():
    pending = create_pending_review()
    url = f"/reviews/{pending['review_id']}/decision"

    first = client.post(
        url,
        json={"decision": "approve", "reviewer": "reviewer-demo"},
    )
    second = client.post(
        url,
        json={"decision": "reject", "reviewer": "reviewer-demo"},
    )

    assert first.status_code == 200
    assert second.status_code == 409

    review = client.get(f"/reviews/{pending['review_id']}")
    assert review.json()["review_status"] == "approved"


def test_get_review_returns_current_decision():
    pending = create_pending_review()
    url = f"/reviews/{pending['review_id']}/decision"
    decision = client.post(
        url,
        json={"decision": "reject", "reviewer": "reviewer-demo"},
    )
    assert decision.status_code == 200

    response = client.get(f"/reviews/{pending['review_id']}")
    assert response.status_code == 200
    assert response.json()["review_status"] == "rejected"
    assert response.json()["reviewer"] == "reviewer-demo"
