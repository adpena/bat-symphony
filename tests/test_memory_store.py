import tempfile
from pathlib import Path

from bat_symphony.memory.store import MemoryStore


def test_append_and_read():
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(state_dir=Path(tmp))
        store.append(event_type="task", data={"issue": "VER-1", "model": "qwen3.5:9b", "outcome": "success"})
        store.append(event_type="correction", data={"before": "used grep", "after": "use Glob"})
        events = store.read_recent(limit=10)
        assert len(events) == 2
        assert events[0]["type"] == "task"
        assert events[1]["type"] == "correction"


def test_read_by_type():
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(state_dir=Path(tmp))
        store.append(event_type="task", data={"outcome": "success"})
        store.append(event_type="correction", data={"note": "fix"})
        store.append(event_type="task", data={"outcome": "failure"})
        tasks = store.read_recent(limit=10, event_type="task")
        assert len(tasks) == 2
        assert all(e["type"] == "task" for e in tasks)


def test_count():
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(state_dir=Path(tmp))
        assert store.count() == 0
        store.append(event_type="task", data={})
        store.append(event_type="task", data={})
        assert store.count() == 2
