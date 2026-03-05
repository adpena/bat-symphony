import pytest
from unittest.mock import AsyncMock, MagicMock
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.memory.reflection import ReflectionEngine


@pytest.mark.asyncio
async def test_reflect_not_enough_data(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    cfg.reflect_every_n = 10
    memory = MemoryStore(state_dir=cfg.state_dir)
    ollama = MagicMock()
    engine = ReflectionEngine(cfg, memory, ollama)
    patterns = await engine.reflect()
    assert patterns == []


def test_parse_patterns():
    cfg = Config()
    memory = MagicMock()
    ollama = MagicMock()
    engine = ReflectionEngine(cfg, memory, ollama)

    # Test plain JSON
    result = engine._parse_patterns('{"patterns": [{"name": "test", "occurrences": 3}]}')
    assert len(result) == 1
    assert result[0]["name"] == "test"

    # Test with markdown fences
    result = engine._parse_patterns('```json\n{"patterns": [{"name": "fenced"}]}\n```')
    assert len(result) == 1
    assert result[0]["name"] == "fenced"

    # Test invalid
    result = engine._parse_patterns("no json here")
    assert result == []
