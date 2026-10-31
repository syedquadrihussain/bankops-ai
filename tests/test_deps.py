import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import auth, deps

SECRET = "a" * 40

mini = FastAPI()


@mini.get("/any-user")
def any_user(user: dict = Depends(deps.current_user)):
    return user


@mini.get("/reviewers-only")
def reviewers_only(user: dict = Depends(deps.require_role("reviewer"))):
    return user


client = TestClient(mini)


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    monkeypatch.setenv("JWT_SECRET", SECRET)


def bearer(token):
    return {"Authorization": "Bearer " + token}


def test_missing_token_returns_401():
    response = client.get("/any-user")
    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_garbage_token_returns_401():
    response = client.get("/any-user", headers=bearer("not-a-token"))
    assert response.status_code == 401


def test_expired_token_returns_401():
    token = auth.create_access_token("asha", "reviewer", minutes=-1)
    assert client.get("/any-user", headers=bearer(token)).status_code == 401


def test_valid_token_returns_the_user():
    token = auth.create_access_token("asha", "analyst")
    response = client.get("/any-user", headers=bearer(token))
    assert response.status_code == 200
    assert response.json() == {"username": "asha", "role": "analyst"}


def test_wrong_role_returns_403():
    token = auth.create_access_token("asha", "analyst")
    response = client.get("/reviewers-only", headers=bearer(token))
    assert response.status_code == 403


def test_right_role_is_allowed():
    token = auth.create_access_token("ravi", "reviewer")
    response = client.get("/reviewers-only", headers=bearer(token))
    assert response.status_code == 200
    assert response.json()["username"] == "ravi"
