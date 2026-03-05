"""Shared memory federation — cross-machine knowledge sync."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import httpx

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore

logger = logging.getLogger("bat_symphony.shared_memory")


class SharedMemory:
    """Federated memory layer across BAT00 and Mac."""

    def __init__(self, config: Config, memory: MemoryStore):
        self.config = config
        self.memory = memory
        self._shared_dir = config.state_dir / "shared"
        self._shared_dir.mkdir(parents=True, exist_ok=True)
        self._knowledge_file = self._shared_dir / "knowledge.jsonl"
        self._client = httpx.AsyncClient(timeout=10.0)
        self._mac_url = f"http://{config.mac_host}:{config.mac_symphony_port}/api/v1"

    async def close(self):
        await self._client.aclose()

    def store(self, key: str, value: Any, source: str = "bat00", tags: list[str] | None = None) -> dict[str, Any]:
        """Store a knowledge entry locally."""
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "key": key,
            "value": value,
            "source": source,
            "tags": tags or [],
        }
        with open(self._knowledge_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return entry

    def retrieve(self, key: str | None = None, tags: list[str] | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieve knowledge entries by key or tags."""
        if not self._knowledge_file.exists():
            return []
        results = []
        with open(self._knowledge_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if key and entry.get("key") != key:
                    continue
                if tags and not any(t in entry.get("tags", []) for t in tags):
                    continue
                results.append(entry)
        return results[-limit:]

    async def sync_to_remote(self, entries: list[dict[str, Any]] | None = None) -> int:
        """Push local knowledge to Mac (best-effort)."""
        if entries is None:
            entries = self.retrieve(limit=100)
        if not entries:
            return 0
        try:
            resp = await self._client.post(
                f"{self._mac_url}/memory/upsert",
                json={"entries": entries, "source": "bat00"},
            )
            if resp.status_code == 200:
                return len(entries)
            logger.warning("Remote sync failed: %d", resp.status_code)
        except httpx.HTTPError as e:
            logger.debug("Remote memory unreachable: %s", e)
        return 0

    async def sync_from_remote(self, tags: list[str] | None = None, limit: int = 50) -> list[dict[str, Any]]:
        """Pull knowledge from Mac (best-effort)."""
        try:
            resp = await self._client.post(
                f"{self._mac_url}/memory/query",
                json={"tags": tags or [], "limit": limit},
            )
            if resp.status_code == 200:
                entries = resp.json().get("entries", [])
                for e in entries:
                    e["source"] = e.get("source", "mac")
                    self.store(e.get("key", ""), e.get("value"), source=e["source"], tags=e.get("tags", []))
                return entries
        except httpx.HTTPError as e:
            logger.debug("Remote memory unreachable: %s", e)
        return []
