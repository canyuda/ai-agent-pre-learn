"""main.py 接口冒烟测试。"""

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_read_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_health_check() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
