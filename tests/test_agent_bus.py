import pytest
from bat_symphony.bridge.agent_bus import AgentBusBridge
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore


def test_publish_and_read_local(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    memory = MemoryStore(state_dir=cfg.state_dir)
    bus = AgentBusBridge(cfg, memory)

    bus.publish_local("test-channel", {"content": "hello"})
    bus.publish_local("test-channel", {"content": "world"})

    msgs = bus.read_local("test-channel")
    assert len(msgs) == 2
    assert msgs[0]["content"] == "hello"
    assert msgs[1]["content"] == "world"
    assert msgs[0]["source"] == "bat00"


def test_list_channels(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    memory = MemoryStore(state_dir=cfg.state_dir)
    bus = AgentBusBridge(cfg, memory)

    bus.publish_local("alpha", {"msg": "a"})
    bus.publish_local("beta", {"msg": "b"})
    channels = bus.list_channels()
    assert "alpha" in channels
    assert "beta" in channels


def test_bounded_channel(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    memory = MemoryStore(state_dir=cfg.state_dir)
    bus = AgentBusBridge(cfg, memory)

    for i in range(600):
        bus.publish_local("flood", {"i": i})
    msgs = bus.read_local("flood")
    assert len(msgs) <= 500
