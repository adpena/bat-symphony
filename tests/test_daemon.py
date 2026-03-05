from fastapi.testclient import TestClient

from bat_symphony.config import Config
from bat_symphony.daemon import BatSymphonyDaemon


def test_daemon_creates_app(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    daemon = BatSymphonyDaemon(cfg)
    assert daemon.app is not None
    client = TestClient(daemon.app)
    resp = client.get("/health")
    assert resp.status_code == 200


def test_daemon_has_memory(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    daemon = BatSymphonyDaemon(cfg)
    assert daemon.memory is not None
    daemon.memory.append(event_type="test", data={"msg": "hello"})
    assert daemon.memory.count() == 1
