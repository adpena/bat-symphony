from bat_symphony.agents.base import AgentConfig, get_llm_config
from bat_symphony.agents.builtin import ALL_AGENTS
from bat_symphony.agents.router import AgentRouter
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore


def test_agent_config():
    cfg = AgentConfig(name="test", description="A test agent")
    assert cfg.name == "test"
    assert cfg.tools == []


def test_get_llm_config():
    cfg = Config()
    llm = get_llm_config(cfg)
    assert "model" in llm
    assert llm["model_server"].endswith("/v1")
    assert llm["api_key"] == "ollama"


def test_builtin_agents_exist():
    assert "code_reviewer" in ALL_AGENTS
    assert "commit_analyzer" in ALL_AGENTS
    assert "task_planner" in ALL_AGENTS
    assert len(ALL_AGENTS) >= 4


def test_router_list_agents(tmp_path):
    cfg = Config()
    cfg.state_dir = tmp_path / "state"
    cfg.state_dir.mkdir()
    memory = MemoryStore(state_dir=cfg.state_dir)
    router = AgentRouter(cfg, memory)
    agents = router.list_agents()
    assert len(agents) >= 4
    names = [a["name"] for a in agents]
    assert "code_reviewer" in names
