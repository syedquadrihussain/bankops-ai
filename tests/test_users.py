import pytest

from app import users

PASSWORD = "Correct-horse-1"


def test_hash_is_not_the_password_and_uses_a_random_salt():
    first = users.hash_password(PASSWORD)
    second = users.hash_password(PASSWORD)
    assert PASSWORD not in first
    assert first != second


def test_verify_password_accepts_right_and_rejects_wrong():
    stored = users.hash_password(PASSWORD)
    assert users.verify_password(PASSWORD, stored) is True
    assert users.verify_password("wrong-password", stored) is False
    assert users.verify_password(PASSWORD, "not-a-valid-hash") is False


def test_create_user_and_authenticate():
    created = users.create_user("  Asha ", PASSWORD, "reviewer")
    assert created == {"username": "asha", "role": "reviewer"}
    assert users.authenticate("ASHA", PASSWORD) == {
        "username": "asha",
        "role": "reviewer",
    }


def test_wrong_password_or_unknown_user_returns_none():
    users.create_user("asha", PASSWORD, "analyst")
    assert users.authenticate("asha", "wrong-password") is None
    assert users.authenticate("nobody", PASSWORD) is None


def test_duplicate_username_is_refused():
    users.create_user("asha", PASSWORD, "analyst")
    with pytest.raises(ValueError):
        users.create_user("Asha", PASSWORD, "reviewer")


def test_invalid_role_is_refused():
    with pytest.raises(ValueError):
        users.create_user("asha", PASSWORD, "admin")


def test_short_password_is_refused():
    with pytest.raises(ValueError):
        users.create_user("asha", "short", "analyst")


def test_password_is_not_stored_in_plain_text():
    users.create_user("asha", PASSWORD, "analyst")
    with users._connection() as conn:
        stored = conn.execute(
            "SELECT password_hash FROM users WHERE username = 'asha'"
        ).fetchone()["password_hash"]
    assert PASSWORD not in stored
    assert stored.startswith("scrypt$")
