import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.learner.loop import LearningLoop


def test_should_reflect():
    cfg = Config()
    cfg.reflect_every_n = 3
    memory = MagicMock()
    ollama = MagicMock()
    loop = LearningLoop(cfg, memory, ollama)

    assert not loop.should_reflect()
    assert not loop.should_reflect()
    assert loop.should_reflect()  # 3rd call


@pytest.mark.asyncio
async def test_run_cycle_no_patterns(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    cfg.reflect_every_n = 1
    memory = MemoryStore(state_dir=cfg.state_dir)
    ollama = MagicMock()
    loop = LearningLoop(cfg, memory, ollama)

    # Mock reflection to return no patterns
    loop.reflection.reflect = AsyncMock(return_value=[])
    result = await loop.run_cycle()
    assert result["patterns_found"] == 0
    assert result["skills_crystallized"] == 0
