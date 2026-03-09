from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_auth_list():
    """GET /auth/ should return a JSON message with the authentication route."""
    response = client.get("/auth/")
    assert response.status_code == 200
    assert response.json() == {"message": "Authentication route"}
