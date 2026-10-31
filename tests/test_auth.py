import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app import auth, users
from app.main import app

client = TestClient(app)
SECRET_A = "a" * 40
SECRET_B = "b" * 40
PASSWORD = "Correct-horse-1"


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET_A)


def test_token_round_trip_keeps_name_and_role():
    token = auth.create_access_token("asha", "reviewer")
    assert auth.decode_access_token(token) == {
        "username": "asha",
        "role": "reviewer",
    }


def test_expired_token_is_rejected():
    token = auth.create_access_token("asha", "reviewer", minutes=-1)
    with pytest.raises(auth.AuthError):
        auth.decode_access_token(token)


def test_token_signed_with_another_secret_is_rejected(monkeypatch):
    token = auth.create_access_token("asha", "reviewer")
    monkeypatch.setenv("JWT_SECRET", SECRET_B)
    with pytest.raises(auth.AuthError):
        auth.decode_access_token(token)


def test_unsigned_token_is_rejected():
    forged = jwt.encode(
        {"sub": "mallory", "role": "reviewer", "exp": int(time.time()) + 600},
        None,
        algorithm="none",
    )
    with pytest.raises(auth.AuthError):
        auth.decode_access_token(forged)


def test_missing_or_short_secret_stops_the_app(monkeypatch):
    monkeypatch.delenv("JWT_SECRET", raising=False)
    with pytest.raises(RuntimeError):
        auth.create_access_token("asha", "reviewer")
    monkeypatch.setenv("JWT_SECRET", "too-short")
    with pytest.raises(RuntimeError):
        auth.create_access_token("asha", "reviewer")


def test_login_returns_a_token_with_the_right_role():
    users.create_user("asha", PASSWORD, "reviewer")
    response = client.post(
        "/login", json={"username": "Asha", "password": PASSWORD}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["role"] == "reviewer"
    assert auth.decode_access_token(body["access_token"]) == {
        "username": "asha",
        "role": "reviewer",
    }


def test_login_wrong_password_returns_401():
    users.create_user("asha", PASSWORD, "reviewer")
    response = client.post(
        "/login", json={"username": "asha", "password": "wrong-password"}
    )
    assert response.status_code == 401
    assert "access_token" not in response.json()


def test_login_unknown_user_gives_the_same_401_message():
    users.create_user("asha", PASSWORD, "reviewer")
    wrong = client.post(
        "/login", json={"username": "asha", "password": "wrong-password"}
    )
    unknown = client.post(
        "/login", json={"username": "nobody", "password": PASSWORD}
    )
    assert unknown.status_code == 401
    assert unknown.json() == wrong.json()
