from bat_symphony.bridge.telemetry import TelemetryCollector
from bat_symphony.config import Config


def test_emit_and_query(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    tc = TelemetryCollector(cfg)

    tc.emit("vertigo", "build_started", severity="info")
    tc.emit("bat00", "reflection_complete", {"patterns": 3}, severity="info")
    tc.emit("vertigo", "test_failed", severity="error")

    all_events = tc.query()
    assert len(all_events) == 3

    vertigo_events = tc.query(source="vertigo")
    assert len(vertigo_events) == 2

    errors = tc.query(severity="error")
    assert len(errors) == 1


def test_summary(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    tc = TelemetryCollector(cfg)

    tc.emit("vertigo", "build", severity="info")
    tc.emit("molt", "deploy", severity="info")
    tc.emit("bat00", "error", severity="error")

    s = tc.summary()
    assert s["total_events"] == 3
    assert s["by_source"]["vertigo"] == 1
    assert s["by_severity"]["error"] == 1
