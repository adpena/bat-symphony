from fastapi.testclient import TestClient

from bat_symphony.bridge.http_server import create_app
from bat_symphony.config import Config


def test_health_endpoint():
    cfg = Config()
    app = create_app(cfg)
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "uptime_s" in data
    assert data["status"] in ("ok", "degraded")


def test_skills_endpoint_empty():
    cfg = Config()
    app = create_app(cfg)
    client = TestClient(app)
    resp = client.get("/skills")
    assert resp.status_code == 200
    assert resp.json() == {"skills": []}
