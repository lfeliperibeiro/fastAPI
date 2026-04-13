"""Testes para /users — listagem, detalhe e atualização de usuários."""

import pytest
from tests.conftest import _make_user


# ---------------------------------------------------------------------------
# GET /users/
# ---------------------------------------------------------------------------

def test_users_root(user_client):
    client, user, session = user_client
    response = client.get("/users/")
    assert response.status_code == 200
    assert response.json() == {"message": "Users routes"}


# ---------------------------------------------------------------------------
# GET /users/users
# ---------------------------------------------------------------------------

def test_get_users_returns_list(user_client):
    client, user, session = user_client
    response = client.get("/users/users")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert isinstance(data["users"], list)
    assert len(data["users"]) >= 1


def test_get_users_fields(user_client):
    client, user, session = user_client
    response = client.get("/users/users")
    assert response.status_code == 200
    first = response.json()["users"][0]
    for field in ("id", "name", "email", "active", "admin"):
        assert field in first


# ---------------------------------------------------------------------------
# GET /users/user/{user_id}
# ---------------------------------------------------------------------------

def test_get_user_by_id_success(user_client):
    client, user, session = user_client
    response = client.get(f"/users/user/{user.id}")
    assert response.status_code == 200
    data = response.json()["user"]
    assert data["id"] == user.id
    assert data["email"] == user.email


def test_get_user_not_found(user_client):
    client, user, session = user_client
    response = client.get("/users/user/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# PUT /users/user/{user_id} — apenas admin
# ---------------------------------------------------------------------------

def test_update_user_as_admin(admin_client):
    client, admin, session = admin_client
    target = _make_user(session, email="target@test.com")

    payload = {
        "name": "Novo Nome",
        "email": "novo@test.com",
        "active": False,
        "admin": False,
    }
    response = client.put(f"/users/user/{target.id}", json=payload)
    assert response.status_code == 200
    assert "successfully" in response.json()["message"]


def test_update_user_as_non_admin_forbidden(user_client):
    client, user, session = user_client
    payload = {
        "name": "Hacker",
        "email": "hacker@test.com",
        "active": True,
        "admin": True,
    }
    response = client.put(f"/users/user/{user.id}", json=payload)
    assert response.status_code == 403
    assert "administrator" in response.json()["detail"].lower()


def test_update_user_not_found(admin_client):
    client, admin, session = admin_client
    payload = {
        "name": "Ghost",
        "email": "ghost@test.com",
        "active": True,
        "admin": False,
    }
    response = client.put("/users/user/99999", json=payload)
    assert response.status_code == 404
