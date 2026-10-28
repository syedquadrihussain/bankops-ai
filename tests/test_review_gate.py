from fastapi.testclient import TestClient

from app.main import app
from app.research_graph import research_graph


client = TestClient(app)


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
    response = client.post(
        "/research",
        json={"question": "identity verification", "limit": 5},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "passed"
    assert body["review_status"] == "pending_review"
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
