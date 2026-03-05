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

    return app
