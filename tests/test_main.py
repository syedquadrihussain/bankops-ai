from fastapi.testclient import TestClient

from app.main import app
import app.main as main_module


client = TestClient(app)


def test_research_finds_matching_policy():
    response = client.post(
        "/research",
        json={
            "question": "identity verification",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] > 0
    assert data["status"] == "research_completed"
    assert data["results"][0]["policy_id"] == "KYC-001"


def test_research_returns_no_matching_policies():
    response = client.post(
        "/research",
        json={
            "question": "space travel rewards",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 0
    assert data["results"] == []
    assert data["status"] == "no_matching_policies"


def test_research_rejects_empty_question():
    response = client.post(
        "/research",
        json={
            "question": "",
            "limit": 5,
        },
    )

    assert response.status_code == 422


def test_research_blocks_results_when_verification_fails(monkeypatch):
    fake_result = {
        "results": [
            {
                "policy_id": "KYC-001",
                "title": "Synthetic KYC Policy",
                "version": "1.0",
                "effective_date": "2026-01-01",
                "category": "KYC",
                "content": "Synthetic test content",
            }
        ],
        "status": "research_completed",
        "verification_status": "failed",
    }

    monkeypatch.setattr(
        main_module.research_graph,
        "invoke",
        lambda state: fake_result,
    )

    response = client.post(
        "/research",
        json={
            "question": "identity verification",
            "limit": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "verification_failed"
    assert data["verification_status"] == "failed"
    assert data["count"] == 0
    assert data["results"] == []