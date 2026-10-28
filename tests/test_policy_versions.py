import json

import pytest

from app import policy_store


def test_compare_kyc_versions():
    result = policy_store.compare_policy_versions("KYC-001")
    assert result is not None
    assert result["old_version"] == "1.0"
    assert result["new_version"] == "2.0"
    assert result["changes"]["content"]["changed"] is True


def test_compare_single_version_policy_returns_none():
    assert policy_store.compare_policy_versions("AML-001") is None


def test_blank_required_field_raises_value_error(monkeypatch, tmp_path):
    path = tmp_path / "policies.json"
    path.write_text(json.dumps([{
        "policy_id": "KYC-001",
        "title": "   ",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "category": "KYC",
        "content": "Example",
    }]), encoding="utf-8")
    monkeypatch.setattr(policy_store, "POLICY_FILE", path)
    with pytest.raises(ValueError, match="title"):
        policy_store.load_policies()


def test_duplicate_policy_version_raises_value_error(monkeypatch, tmp_path):
    policy = {
        "policy_id": "KYC-001",
        "title": "KYC Policy",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "category": "KYC",
        "content": "Example",
    }
    path = tmp_path / "policies.json"
    path.write_text(json.dumps([policy, policy]), encoding="utf-8")
    monkeypatch.setattr(policy_store, "POLICY_FILE", path)
    with pytest.raises(ValueError, match="Duplicate"):
        policy_store.load_policies()
