from bat_symphony.config import Config


def test_defaults():
    cfg = Config()
    assert cfg.ollama_url == "http://localhost:11434"
    assert cfg.http_port == 8787
    assert cfg.state_dir.name == "state"
    assert cfg.default_model == "qwen3.5:9b"
    assert cfg.reflect_every_n == 10
    assert cfg.skill_threshold_uses == 2
    assert cfg.skill_threshold_success == 0.5


def test_env_override(monkeypatch):
    monkeypatch.setenv("BAT_OLLAMA_URL", "http://other:9999")
    monkeypatch.setenv("BAT_HTTP_PORT", "9000")
    monkeypatch.setenv("BAT_DEFAULT_MODEL", "qwen3.5:27b")
    cfg = Config()
    assert cfg.ollama_url == "http://other:9999"
    assert cfg.http_port == 9000
    assert cfg.default_model == "qwen3.5:27b"
