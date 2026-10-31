import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import review_store
from app.main import app

client = TestClient(app)
RESULTS = [{"policy_id": "KYC-001", "version": "1.0"}]


def test_creating_a_review_writes_an_audit_event():
    review_id = review_store.create_review("identity", RESULTS)
    events = review_store.get_audit_log(review_id)
    assert [e["event"] for e in events] == ["review_created"]
    assert events[0]["actor"] == "system"


def test_decision_is_audited_with_the_reviewer():
    review_id = review_store.create_review("identity", RESULTS)
    review_store.decide_review(review_id, "approved", "reviewer-demo")
    events = review_store.get_audit_log(review_id)
    assert [e["event"] for e in events] == ["review_created", "review_approved"]
    assert events[1]["actor"] == "reviewer-demo"


def test_refused_second_decision_is_audited_and_first_one_stays():
    review_id = review_store.create_review("identity", RESULTS)
    review_store.decide_review(review_id, "approved", "first")
    review_store.decide_review(review_id, "rejected", "second")
    events = review_store.get_audit_log(review_id)
    assert [e["event"] for e in events] == [
        "review_created", "review_approved", "decision_refused",
    ]
    assert review_store.get_review(review_id)["review_status"] == "approved"


def test_audit_log_cannot_be_changed_or_deleted():
    review_id = review_store.create_review("identity", RESULTS)
    with pytest.raises(sqlite3.DatabaseError):
        with review_store._connection() as conn:
            conn.execute("DELETE FROM audit_log")
    with pytest.raises(sqlite3.DatabaseError):
        with review_store._connection() as conn:
            conn.execute("UPDATE audit_log SET actor = 'someone-else'")
    assert len(review_store.get_audit_log(review_id)) == 1


def test_audit_endpoint_lists_events_in_order():
    pending = client.post(
        "/research", json={"question": "identity verification", "limit": 1}
    ).json()
    review_id = pending["review_id"]
    client.post(
        f"/reviews/{review_id}/decision",
        json={"decision": "reject", "reviewer": "reviewer-demo"},
    )
    response = client.get(f"/reviews/{review_id}/audit")
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [e["event"] for e in body["events"]] == ["review_created", "review_rejected"]


def test_audit_endpoint_unknown_review_returns_404():
    assert client.get("/reviews/not-a-real-review/audit").status_code == 404
