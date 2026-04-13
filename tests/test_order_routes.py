"""Testes para /orders — cobrindo criação, edição, cancelamento, conclusão e listagens."""

import pytest
from tests.conftest import _make_user, _make_product


# ---------------------------------------------------------------------------
# GET /orders/ (autenticado)
# ---------------------------------------------------------------------------

def test_orders_root(user_client):
    client, user, session = user_client
    response = client.get("/orders/")
    assert response.status_code == 200
    assert response.json() == {"message": "List of orders"}


# ---------------------------------------------------------------------------
# POST /orders/order — criar pedido
# ---------------------------------------------------------------------------

def test_create_order_success(user_client):
    client, user, session = user_client
    product = _make_product(session)

    payload = {
        "user_id": user.id,
        "products": [{"product_id": product.id, "quantity": 2}],
        "notes": "Sem cebola",
        "payment_method": "credit_card",
    }
    response = client.post("/orders/order", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["total_price"] == product.price * 2
    assert data["notes"] == "Sem cebola"
    assert data["payment_method"] == "credit_card"


def test_create_order_no_products(user_client):
    client, user, session = user_client
    payload = {"user_id": user.id, "products": []}
    response = client.post("/orders/order", json=payload)
    assert response.status_code == 400
    assert "product" in response.json()["detail"].lower()


def test_create_order_product_not_found(user_client):
    client, user, session = user_client
    payload = {
        "user_id": user.id,
        "products": [{"product_id": 99999, "quantity": 1}],
    }
    response = client.post("/orders/order", json=payload)
    assert response.status_code == 404


def test_create_order_zero_quantity(user_client):
    client, user, session = user_client
    product = _make_product(session)
    payload = {
        "user_id": user.id,
        "products": [{"product_id": product.id, "quantity": 0}],
    }
    response = client.post("/orders/order", json=payload)
    assert response.status_code == 400
    assert "Quantity" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /orders/order/add_product — criar produto avulso
# ---------------------------------------------------------------------------

def test_add_product_success(user_client):
    client, user, session = user_client
    payload = {"name": "Produto Teste", "price": 15.0, "size": "G"}
    response = client.post("/orders/order/add_product", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 15.0
    assert "product_id" in data


# ---------------------------------------------------------------------------
# POST /orders/order/remove_product/{id}
# ---------------------------------------------------------------------------

def test_remove_product_success(user_client):
    client, user, session = user_client
    product = _make_product(session, name="Para remover")
    response = client.post(f"/orders/order/remove_product/{product.id}")
    assert response.status_code == 200
    assert str(product.id) in response.json()["message"]


def test_remove_product_not_found(user_client):
    client, user, session = user_client
    response = client.post("/orders/order/remove_product/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /orders/order/cancel/{order_id}
# ---------------------------------------------------------------------------

def _create_order_via_api(client, user, session):
    """Helper para criar um pedido e retornar o order_id."""
    product = _make_product(session)
    payload = {
        "user_id": user.id,
        "products": [{"product_id": product.id, "quantity": 1}],
    }
    r = client.post("/orders/order", json=payload)
    assert r.status_code == 200
    return r.json()["order_id"]


def test_cancel_order_success(user_client):
    client, user, session = user_client
    order_id = _create_order_via_api(client, user, session)
    response = client.post(f"/orders/order/cancel/{order_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"


def test_cancel_order_not_found(user_client):
    client, user, session = user_client
    response = client.post("/orders/order/cancel/99999")
    assert response.status_code == 404


def test_cancel_order_permission_denied(user_client, db_session):
    """Usuário não pode cancelar pedido de outro usuário."""
    client, user, session = user_client
    other_user = _make_user(session, email="other@test.com")
    product = _make_product(session)
    payload = {
        "user_id": other_user.id,
        "products": [{"product_id": product.id, "quantity": 1}],
    }
    r = client.post("/orders/order", json=payload)
    order_id = r.json()["order_id"]

    response = client.post(f"/orders/order/cancel/{order_id}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /orders/order/finished/{order_id}
# ---------------------------------------------------------------------------

def test_finish_order_success(user_client):
    client, user, session = user_client
    order_id = _create_order_via_api(client, user, session)
    response = client.post(f"/orders/order/finished/{order_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "Finished"


def test_finish_order_not_found(user_client):
    client, user, session = user_client
    response = client.post("/orders/order/finished/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# GET /orders/order/{order_id}
# ---------------------------------------------------------------------------

def test_get_order_success(user_client):
    client, user, session = user_client
    order_id = _create_order_via_api(client, user, session)
    response = client.get(f"/orders/order/{order_id}")
    assert response.status_code == 200
    data = response.json()
    assert "order" in data
    assert "quantity" in data


def test_get_order_not_found(user_client):
    client, user, session = user_client
    response = client.get("/orders/order/99999")
    assert response.status_code == 404


def test_get_order_permission_denied(user_client, db_session):
    """Usuário não pode ver pedido de outro usuário."""
    client, user, session = user_client
    other_user = _make_user(db_session, email="other2@test.com")
    product = _make_product(session)
    payload = {
        "user_id": other_user.id,
        "products": [{"product_id": product.id, "quantity": 1}],
    }
    r = client.post("/orders/order", json=payload)
    order_id = r.json()["order_id"]

    response = client.get(f"/orders/order/{order_id}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /orders/list_order/order_user — pedidos do usuário logado
# ---------------------------------------------------------------------------

def test_list_orders_by_user(user_client):
    client, user, session = user_client
    _create_order_via_api(client, user, session)
    _create_order_via_api(client, user, session)
    response = client.get("/orders/list_order/order_user")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    assert "order_id" in data[0]


# ---------------------------------------------------------------------------
# GET /orders/list — apenas admin
# ---------------------------------------------------------------------------

def test_list_all_products_as_admin(admin_client):
    client, admin, session = admin_client
    _make_product(session, name="Prod1")
    _make_product(session, name="Prod2")
    response = client.get("/orders/list")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_all_products_forbidden_for_user(user_client):
    client, user, session = user_client
    response = client.get("/orders/list")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /orders/order/edit/{order_id}
# ---------------------------------------------------------------------------

def test_edit_order_success(user_client):
    client, user, session = user_client
    order_id = _create_order_via_api(client, user, session)
    new_product = _make_product(session, name="Novo Produto", price=25.0)

    payload = {
        "user_id": user.id,
        "products": [{"product_id": new_product.id, "quantity": 3}],
        "notes": "Editado",
        "payment_method": "pix",
    }
    response = client.put(f"/orders/order/edit/{order_id}", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total_price"] == 25.0 * 3
    assert data["notes"] == "Editado"


def test_edit_order_not_found(user_client):
    client, user, session = user_client
    payload = {
        "user_id": user.id,
        "products": [{"product_id": 1, "quantity": 1}],
    }
    response = client.put("/orders/order/edit/99999", json=payload)
    assert response.status_code == 404


def test_edit_order_permission_denied(user_client, db_session):
    """Usuário não pode editar pedido de outro."""
    client, user, session = user_client
    other = _make_user(db_session, email="other3@test.com")
    product = _make_product(session)
    payload_create = {
        "user_id": other.id,
        "products": [{"product_id": product.id, "quantity": 1}],
    }
    r = client.post("/orders/order", json=payload_create)
    order_id = r.json()["order_id"]

    new_product = _make_product(session, name="X")
    payload_edit = {
        "user_id": user.id,
        "products": [{"product_id": new_product.id, "quantity": 1}],
    }
    response = client.put(f"/orders/order/edit/{order_id}", json=payload_edit)
    assert response.status_code == 403


def test_admin_can_cancel_any_order(admin_client, db_session):
    """Admin pode cancelar pedido de qualquer usuário."""
    client, admin, session = admin_client
    other = _make_user(db_session, email="other4@test.com")
    product = _make_product(session)
    payload = {
        "user_id": other.id,
        "products": [{"product_id": product.id, "quantity": 1}],
    }
    r = client.post("/orders/order", json=payload)
    order_id = r.json()["order_id"]

    response = client.post(f"/orders/order/cancel/{order_id}")
    assert response.status_code == 200
    assert response.json()["status"] == "Cancelled"
