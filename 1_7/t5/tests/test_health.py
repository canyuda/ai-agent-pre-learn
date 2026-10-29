from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_reports_ok():
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
