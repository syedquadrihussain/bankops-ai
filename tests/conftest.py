import os

import pytest

# Tokens made when test files load must stay valid while tests run.
os.environ["JWT_SECRET"] = "test-only-secret-" + "x" * 32


@pytest.fixture(autouse=True)
def temporary_review_database(tmp_path, monkeypatch):
    """Give every test its own empty review database."""
    monkeypatch.setenv("BANKOPS_DB", str(tmp_path / "test_reviews.db"))
