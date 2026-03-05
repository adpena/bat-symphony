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

    @app.post("/bus/publish")
    async def bus_publish(channel: str = "general", message: str = "") -> dict[str, Any]:
        """Publish to agent bus."""
        from bat_symphony.bridge.agent_bus import AgentBusBridge
        from bat_symphony.memory.store import MemoryStore
        bus = AgentBusBridge(config, MemoryStore(state_dir=config.state_dir))
        result = await bus.broadcast(channel, {"content": message})
        return {"published": True, "entry": result}

    @app.get("/bus/channels")
    async def bus_channels() -> dict[str, Any]:
        """List agent bus channels."""
        from bat_symphony.bridge.agent_bus import AgentBusBridge
        from bat_symphony.memory.store import MemoryStore
        bus = AgentBusBridge(config, MemoryStore(state_dir=config.state_dir))
        return {"channels": bus.list_channels()}

    @app.post("/telemetry/emit")
    async def telemetry_emit(source: str = "bat00", event: str = "", severity: str = "info") -> dict[str, Any]:
        """Emit a telemetry event."""
        from bat_symphony.bridge.telemetry import TelemetryCollector
        collector = TelemetryCollector(config)
        entry = collector.emit(source=source, event=event, severity=severity)
        return {"emitted": True, "entry": entry}

    @app.get("/telemetry/summary")
    async def telemetry_summary(days: int = 1) -> dict[str, Any]:
        """Get telemetry summary."""
        from bat_symphony.bridge.telemetry import TelemetryCollector
        collector = TelemetryCollector(config)
        return collector.summary(days=days)

    @app.post("/shared/store")
    async def shared_store(key: str = "", value: str = "", tags: str = "") -> dict[str, Any]:
        """Store shared knowledge."""
        from bat_symphony.bridge.shared_memory import SharedMemory
        from bat_symphony.memory.store import MemoryStore
        sm = SharedMemory(config, MemoryStore(state_dir=config.state_dir))
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        entry = sm.store(key=key, value=value, tags=tag_list)
        return {"stored": True, "entry": entry}

    @app.get("/shared/retrieve")
    async def shared_retrieve(key: str | None = None, tags: str = "", limit: int = 50) -> dict[str, Any]:
        """Retrieve shared knowledge."""
        from bat_symphony.bridge.shared_memory import SharedMemory
        from bat_symphony.memory.store import MemoryStore
        sm = SharedMemory(config, MemoryStore(state_dir=config.state_dir))
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
        entries = sm.retrieve(key=key, tags=tag_list, limit=limit)
        return {"entries": entries, "count": len(entries)}

    return app
