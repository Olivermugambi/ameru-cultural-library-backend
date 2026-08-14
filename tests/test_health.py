from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_versioned_api_root() -> None:
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json() == {"version": "v1", "status": "available"}


def test_openapi_metadata() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json()["info"]["title"] == "Ameru Cultural Library API"
