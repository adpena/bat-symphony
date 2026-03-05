from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.learner.crystallizer import Crystallizer


def test_evaluate_patterns_below_threshold(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    cfg.skill_threshold_uses = 5
    cfg.skill_threshold_success = 0.7
    memory = MemoryStore(state_dir=cfg.state_dir)
    c = Crystallizer(cfg, memory)

    patterns = [{"name": "low_pattern", "occurrences": 1, "success_rate": 0.3}]
    ready = c.evaluate_patterns(patterns)
    assert len(ready) == 0


def test_evaluate_and_crystallize(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    cfg.skill_threshold_uses = 2
    cfg.skill_threshold_success = 0.5
    memory = MemoryStore(state_dir=cfg.state_dir)
    c = Crystallizer(cfg, memory)

    patterns = [{"name": "good_pattern", "occurrences": 3, "success_rate": 0.8,
                 "description": "A useful pattern", "category": "workflow",
                 "suggested_skill": "Use this pattern when X"}]
    ready = c.evaluate_patterns(patterns)
    assert len(ready) == 1

    path = c.crystallize_skill(ready[0])
    assert path.exists()
    content = path.read_text()
    assert "good_pattern" in content
    assert "80%" in content
