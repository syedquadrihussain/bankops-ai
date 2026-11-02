from fastapi.testclient import TestClient

from app import agent_graph, auth, review_store
from app.main import app

client = TestClient(app)

FAKE_RESULT = {
    "status": "completed",
    "answer": "KYC-001 needs two items.",
    "tool_calls": [{"name": "get_policy", "args": {"policy_id": "KYC-001"}}],
}


def bearer(username="asha", role="analyst"):
    return {"Authorization": "Bearer " + auth.create_access_token(username, role)}


def test_agent_ask_requires_login():
    response = client.post("/agent/ask", json={"question": "hello"})
    assert response.status_code == 401


def test_agent_ask_needs_a_real_model(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    response = client.post(
        "/agent/ask", json={"question": "hello"}, headers=bearer()
    )
    assert response.status_code == 503


def test_agent_ask_returns_the_answer_and_logs_every_step(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr(agent_graph, "run_agent", lambda question: FAKE_RESULT)
    response = client.post(
        "/agent/ask",
        json={"question": "What does KYC-001 require?"},
        headers=bearer(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["answer"].startswith("KYC-001")
    events = review_store.get_audit_log(body["run_id"])
    assert [e["event"] for e in events] == [
        "agent_question",
        "agent_tool_call",
        "agent_run_finished",
    ]
    assert all(e["actor"] == "asha" for e in events)


def test_agent_ask_rejects_an_empty_question(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    response = client.post(
        "/agent/ask", json={"question": "   "}, headers=bearer()
    )
    assert response.status_code == 422


def test_agent_ask_model_failure_returns_502_and_no_answer(monkeypatch):
    def broken(question):
        raise RuntimeError("model offline")

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setattr(agent_graph, "run_agent", broken)
    response = client.post(
        "/agent/ask", json={"question": "hello"}, headers=bearer()
    )
    assert response.status_code == 502
    assert "answer" not in response.json()
