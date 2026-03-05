from bat_symphony.bridge.shared_memory import SharedMemory
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore


def test_store_and_retrieve(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    memory = MemoryStore(state_dir=cfg.state_dir)
    sm = SharedMemory(cfg, memory)

    sm.store("grapple_tuning", {"force": 50}, tags=["vertigo", "physics"])
    sm.store("bike_drift", {"angle": 15}, tags=["vertigo", "vehicle"])

    all_entries = sm.retrieve()
    assert len(all_entries) == 2

    by_key = sm.retrieve(key="grapple_tuning")
    assert len(by_key) == 1
    assert by_key[0]["value"]["force"] == 50

    by_tag = sm.retrieve(tags=["vehicle"])
    assert len(by_tag) == 1
    assert by_tag[0]["key"] == "bike_drift"
