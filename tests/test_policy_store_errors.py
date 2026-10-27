import pytest

from app import policy_store


def test_missing_policy_file_raises_error(monkeypatch, tmp_path):
    missing_file = tmp_path / "missing_policies.json"

    monkeypatch.setattr(policy_store, "POLICY_FILE", missing_file)

    with pytest.raises(FileNotFoundError):
        policy_store.load_policies()


def test_invalid_json_raises_error(monkeypatch, tmp_path):
    invalid_file = tmp_path / "invalid_policies.json"
    invalid_file.write_text("{invalid json}", encoding="utf-8")

    monkeypatch.setattr(policy_store, "POLICY_FILE", invalid_file)

    with pytest.raises(ValueError):
        policy_store.load_policies()