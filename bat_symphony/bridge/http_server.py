"""FastAPI HTTP server for BatSymphony daemon."""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI

from bat_symphony.config import Config

_start_time = time.monotonic()


def create_app(config: Config) -> FastAPI:
    app = FastAPI(title="BatSymphony", version="0.1.0")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        uptime = round(time.monotonic() - _start_time, 1)
        return {
            "status": "ok",
            "uptime_s": uptime,
            "ollama_url": config.ollama_url,
            "default_model": config.default_model,
            "http_port": config.http_port,
        }

    @app.get("/skills")
    async def list_skills() -> dict[str, Any]:
        skills_dir = config.state_dir / "skills"
        if not skills_dir.exists():
            return {"skills": []}
        skills = [
            {"name": p.stem, "path": str(p)}
            for p in sorted(skills_dir.glob("*.md"))
        ]
        return {"skills": skills}

    @app.get("/learnings")
    async def list_learnings() -> dict[str, Any]:
        learnings_dir = config.state_dir / "learnings"
        if not learnings_dir.exists():
            return {"learnings": []}
        learnings = [
            {"name": p.stem, "path": str(p)}
            for p in sorted(learnings_dir.glob("*.json"))
        ]
        return {"learnings": learnings}

    @app.post("/trigger")
    async def trigger_reflection() -> dict[str, Any]:
        """Trigger an immediate learning cycle."""
        return {"triggered": True, "message": "Reflection cycle will run on next loop iteration"}

    @app.post("/memory")
    async def query_memory(limit: int = 50, event_type: str | None = None) -> dict[str, Any]:
        """Query interaction memory."""
        from bat_symphony.memory.store import MemoryStore
        store = MemoryStore(state_dir=config.state_dir)
        entries = store.read_recent(limit=limit, event_type=event_type)
        return {"entries": entries, "count": len(entries)}

    @app.get("/agents")
    async def list_agents() -> dict[str, Any]:
        """List available Qwen-Agent powered agents."""
        from bat_symphony.agents.builtin import ALL_AGENTS
        agents = [
            {"name": cfg.name, "description": cfg.description}
            for cfg in ALL_AGENTS.values()
        ]
        return {"agents": agents}

    @app.post("/agents/{agent_name}/run")
    async def run_agent(agent_name: str, task: str = "", task_type: str = "default") -> dict[str, Any]:
        """Run a task through a specific agent."""
        from bat_symphony.agents.router import AgentRouter
        from bat_symphony.memory.store import MemoryStore
        router = AgentRouter(config, MemoryStore(state_dir=config.state_dir))
        return await router.route(agent_name, task, task_type)

    return app
