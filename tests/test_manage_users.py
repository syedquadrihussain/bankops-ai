from app import manage_users, users

PASSWORD = "Correct-horse-1"


def run_with(monkeypatch, username, role, passwords):
    answers = iter([username, role])
    secrets_ = iter(passwords)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(secrets_))
    return manage_users.main()


def test_manage_users_creates_a_working_user(monkeypatch):
    code = run_with(monkeypatch, "Asha", "reviewer", [PASSWORD, PASSWORD])
    assert code == 0
    assert users.authenticate("asha", PASSWORD) == {
        "username": "asha",
        "role": "reviewer",
    }


def test_manage_users_refuses_mismatched_passwords(monkeypatch):
    code = run_with(monkeypatch, "asha", "reviewer", [PASSWORD, "different-pass"])
    assert code == 1
    assert users.authenticate("asha", PASSWORD) is None
