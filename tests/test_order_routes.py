from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_orders_list():
    """GET /orders/ should return a JSON message with the list of orders."""
    response = client.get("/orders/")
    assert response.status_code == 200
    assert response.json() == {"message": "List of orders"}
