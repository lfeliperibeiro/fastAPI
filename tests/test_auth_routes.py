"""Testes para /auth — cobrindo signup, login, refresh, forgot/reset password."""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient

from main import app
from tests.conftest import _make_user
from auth_routes import create_password_reset_token, create_token


# ---------------------------------------------------------------------------
# GET /auth/
# ---------------------------------------------------------------------------

def test_auth_root(anon_client):
    """GET /auth/ deve retornar mensagem de rota."""
    response = anon_client.get("/auth/")
    assert response.status_code == 200
    assert response.json() == {"message": "Authentication route"}


# ---------------------------------------------------------------------------
# POST /auth/signup
# ---------------------------------------------------------------------------

def test_signup_success(anon_client):
    payload = {
        "name": "Alice",
        "email": "alice@example.com",
        "password": "StrongPass1",
        "confirm_password": "StrongPass1",
        "active": True,
        "admin": False,
    }
    response = anon_client.post("/auth/signup", json=payload)
    assert response.status_code == 200
    assert "alice@example.com" in response.json()["message"]


def test_signup_duplicate_email(anon_client, db_session):
    _make_user(db_session, email="dup@example.com")
    payload = {
        "name": "Bob",
        "email": "dup@example.com",
        "password": "Pass1234",
        "confirm_password": "Pass1234",
        "active": True,
        "admin": False,
    }
    response = anon_client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signup_password_mismatch(anon_client):
    payload = {
        "name": "Carol",
        "email": "carol@example.com",
        "password": "Pass1234",
        "confirm_password": "Different",
        "active": True,
        "admin": False,
    }
    response = anon_client.post("/auth/signup", json=payload)
    assert response.status_code == 400
    assert "do not match" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

def test_login_success(anon_client, db_session):
    _make_user(db_session, email="login@example.com", password="mypassword")
    payload = {"email": "login@example.com", "password": "mypassword"}
    response = anon_client.post("/auth/login", json=payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Login realizado com sucesso"}
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


def test_login_wrong_password(anon_client, db_session):
    _make_user(db_session, email="wrongpw@example.com", password="correct")
    payload = {"email": "wrongpw@example.com", "password": "wrong"}
    response = anon_client.post("/auth/login", json=payload)
    assert response.status_code == 400
    assert "invalid credentials" in response.json()["detail"]


def test_login_unknown_email(anon_client):
    payload = {"email": "nobody@example.com", "password": "any"}
    response = anon_client.post("/auth/login", json=payload)
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /auth/token  (OAuth2PasswordRequestForm)
# ---------------------------------------------------------------------------

def test_token_endpoint_success(anon_client, db_session):
    _make_user(db_session, email="token@example.com", password="tokenpass")
    response = anon_client.post(
        "/auth/token",
        data={"username": "token@example.com", "password": "tokenpass"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_token_endpoint_invalid(anon_client):
    response = anon_client.post(
        "/auth/token",
        data={"username": "ghost@example.com", "password": "x"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

def test_refresh_token(db_session):
    """Refresh com access_token cookie válido deve devolver novo access_token."""
    user = _make_user(db_session, email="refresh@example.com")
    token = create_token(user.id, duration=timedelta(minutes=30))

    from dependencies import get_session
    app.dependency_overrides[get_session] = lambda: (yield db_session)
    client = TestClient(app)
    client.cookies.set("access_token", token)

    response = client.post("/auth/refresh")
    assert response.status_code == 200
    assert "access_token" in response.json()

    app.dependency_overrides.clear()


def test_refresh_token_invalid(anon_client):
    anon_client.cookies.set("access_token", "invalidtoken")
    response = anon_client.post("/auth/refresh")
    assert response.status_code == 401
    anon_client.cookies.clear()


# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------

def test_forgot_password_existing_email(anon_client, db_session, monkeypatch):
    """Deve retornar mensagem genérica mesmo quando e-mail existe."""
    _make_user(db_session, email="forgot@example.com")
    # Evita envio real de e-mail
    monkeypatch.setattr(
        "auth_routes.send_password_reset_email",
        lambda *args, **kwargs: None,
    )
    response = anon_client.post("/auth/forgot-password", json={"email": "forgot@example.com"})
    assert response.status_code == 200
    assert "receberá" in response.json()["message"]


def test_forgot_password_unknown_email(anon_client):
    """Deve retornar a mesma mensagem genérica para e-mail desconhecido."""
    response = anon_client.post("/auth/forgot-password", json={"email": "ghost@nowhere.com"})
    assert response.status_code == 200
    assert "receberá" in response.json()["message"]


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------

def test_reset_password_success(anon_client, db_session):
    user = _make_user(db_session, email="reset@example.com", password="oldpass")
    token = create_password_reset_token(user.id)

    response = anon_client.post(
        "/auth/reset-password",
        json={"token": token, "password": "newpass123", "confirm_password": "newpass123"},
    )
    assert response.status_code == 200
    assert "sucesso" in response.json()["message"]


def test_reset_password_mismatch(anon_client, db_session):
    user = _make_user(db_session, email="resetmm@example.com")
    token = create_password_reset_token(user.id)

    response = anon_client.post(
        "/auth/reset-password",
        json={"token": token, "password": "abc", "confirm_password": "xyz"},
    )
    assert response.status_code == 400
    assert "coincidem" in response.json()["detail"]


def test_reset_password_invalid_token(anon_client):
    response = anon_client.post(
        "/auth/reset-password",
        json={"token": "badtoken", "password": "abc123", "confirm_password": "abc123"},
    )
    assert response.status_code == 400


# ---------------------------------------------------------------------------
# verify_token via cookie
# ---------------------------------------------------------------------------

def test_verify_token_missing_cookie_returns_401(anon_client):
    """Rota protegida sem cookie deve retornar 401."""
    response = anon_client.get("/users/users")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_verify_token_valid_cookie_passes(anon_client, db_session):
    """Rota protegida com cookie access_token válido deve retornar 200."""
    user = _make_user(db_session, email="cookieuser@example.com")
    token = create_token(user.id)
    anon_client.cookies.set("access_token", token)
    response = anon_client.get("/users/users")
    assert response.status_code == 200
    anon_client.cookies.clear()
