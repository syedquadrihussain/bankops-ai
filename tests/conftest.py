import pytest


@pytest.fixture(autouse=True)
def temporary_review_database(tmp_path, monkeypatch):
    """Give every test its own empty review database."""
    monkeypatch.setenv("BANKOPS_DB", str(tmp_path / "test_reviews.db"))
