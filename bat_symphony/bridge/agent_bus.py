"""Agent bus bridge — connects to Mac's Symphony agent_bus via HTTP."""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore

logger = logging.getLogger("bat_symphony.agent_bus")


class AgentBusBridge:
    """Bidirectional message bridge between BAT00 and Mac agent_bus."""

    def __init__(self, config: Config, memory: MemoryStore):
        self.config = config
        self.memory = memory
        self._local_channels: dict[str, list[dict[str, Any]]] = {}
        self._mac_url = f"http://{config.mac_host}:{config.mac_symphony_port}/api/v1"
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        await self._client.aclose()

    # --- Local bus (BAT00-side) ---

    def publish_local(self, channel: str, message: dict[str, Any]) -> dict[str, Any]:
        """Publish a message to the local bus."""
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "channel": channel,
            "source": "bat00",
            **message,
        }
        if channel not in self._local_channels:
            self._local_channels[channel] = []
        self._local_channels[channel].append(entry)
        # Keep bounded
        if len(self._local_channels[channel]) > 500:
            self._local_channels[channel] = self._local_channels[channel][-250:]
        self.memory.append(event_type="bus_publish", data={"channel": channel, "preview": str(message)[:200]})
        return entry

    def read_local(self, channel: str, limit: int = 50) -> list[dict[str, Any]]:
        """Read recent messages from a local channel."""
        return self._local_channels.get(channel, [])[-limit:]

    def list_channels(self) -> list[str]:
        """List all local channels."""
        return list(self._local_channels.keys())

    # --- Remote bus (Mac-side, best-effort) ---

    async def publish_remote(self, channel: str, message: dict[str, Any]) -> dict[str, Any] | None:
        """Publish a message to the Mac's agent_bus (best-effort)."""
        try:
            resp = await self._client.post(
                f"{self._mac_url}/bus/publish",
                json={"namespace": "vertigo", "channel": channel, "payload": message},
            )
            if resp.status_code == 200:
                return resp.json()
            logger.warning("Remote bus publish failed: %d %s", resp.status_code, resp.text[:200])
        except httpx.HTTPError as e:
            logger.debug("Remote bus unreachable: %s", e)
        return None

    async def fetch_remote(self, channel: str, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch recent messages from the Mac's agent_bus (best-effort)."""
        try:
            resp = await self._client.post(
                f"{self._mac_url}/bus/fetch",
                json={"namespace": "vertigo", "channel": channel, "limit": limit},
            )
            if resp.status_code == 200:
                return resp.json().get("messages", [])
        except httpx.HTTPError as e:
            logger.debug("Remote bus unreachable: %s", e)
        return []

    # --- Cross-publish (local + remote) ---

    async def broadcast(self, channel: str, message: dict[str, Any]) -> dict[str, Any]:
        """Publish to both local and remote bus."""
        local = self.publish_local(channel, message)
        await self.publish_remote(channel, message)
        return local
