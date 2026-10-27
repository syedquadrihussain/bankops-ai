from app.policy_store import load_policies, search_policies, get_policy


def test_load_policies():
    policies = load_policies()
    assert len(policies) == 3


def test_get_existing_policy():
    policy = get_policy("KYC-001")
    assert policy is not None
    assert policy["category"] == "KYC"


def test_get_policy_is_case_insensitive():
    policy = get_policy("kyc-001")
    assert policy is not None
    assert policy["policy_id"] == "KYC-001"


def test_get_missing_policy():
    assert get_policy("UNKNOWN-999") is None


def test_search_identity_policy():
    results = search_policies("identity verification")
    assert results
    assert results[0]["policy_id"] == "KYC-001"


def test_empty_search():
    assert search_policies("") == []


def test_search_limit():
    results = search_policies("policy", limit=1)
    assert len(results) <= 1


def test_invalid_search_limit():
    try:
        search_policies("policy", limit=0)
        assert False, "Expected ValueError for limit=0"
    except ValueError:
        pass
