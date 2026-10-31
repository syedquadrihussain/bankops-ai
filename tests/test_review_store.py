from app import review_store

RESULTS = [{"policy_id": "KYC-001", "version": "1.0"}]


def test_created_review_is_pending_and_can_be_read_back():
    review_id = review_store.create_review("identity", RESULTS)
    record = review_store.get_review(review_id)
    assert record["review_status"] == "pending_review"
    assert record["question"] == "identity"
    assert record["results"] == RESULTS
    assert record["decided_at"] is None
    assert record["reviewer"] is None


def test_review_is_stored_in_a_file(tmp_path):
    review_store.create_review("identity", RESULTS)
    assert (tmp_path / "test_reviews.db").exists()


def test_unknown_review_returns_none_and_not_found():
    assert review_store.get_review("missing") is None
    outcome, record = review_store.decide_review("missing", "approved", "demo")
    assert outcome == "not_found"
    assert record is None


def test_decision_is_saved():
    review_id = review_store.create_review("identity", RESULTS)
    outcome, record = review_store.decide_review(review_id, "approved", "reviewer-demo")
    assert outcome == "decided"
    assert record["review_status"] == "approved"
    saved = review_store.get_review(review_id)
    assert saved["reviewer"] == "reviewer-demo"
    assert saved["decided_at"]


def test_second_decision_is_refused_and_first_one_stays():
    review_id = review_store.create_review("identity", RESULTS)
    review_store.decide_review(review_id, "approved", "first")
    outcome, record = review_store.decide_review(review_id, "rejected", "second")
    assert outcome == "already_decided"
    assert record is None
    assert review_store.get_review(review_id)["review_status"] == "approved"
