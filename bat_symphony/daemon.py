"""Main BatSymphony daemon - event loop, wiring, lifecycle."""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

import uvicorn
from fastapi import FastAPI

from bat_symphony.bridge.http_server import create_app
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.ollama import OllamaClient
from bat_symphony.watchers.git_watcher import GitWatcher

logger = logging.getLogger("bat_symphony")


class BatSymphonyDaemon:
    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self.memory = MemoryStore(state_dir=self.config.state_dir)
        self.ollama = OllamaClient(base_url=self.config.ollama_url)
        self.git_watcher = GitWatcher(repos=self.config.watch_repos)
        self.app: FastAPI = create_app(self.config)
        self._running = False

    async def _git_poll_loop(self):
        while self._running:
            changes = self.git_watcher.poll()
            for change in changes:
                logger.info(
                    "Git change in %s: %s -> %s",
                    change["repo"],
                    change["old_head"][:8],
                    change["new_head"][:8],
                )
                self.memory.append(event_type="git_change", data=change)
            await asyncio.sleep(self.config.git_poll_interval_s)

    async def _health_check_loop(self):
        while self._running:
            healthy = await self.ollama.health()
            if not healthy:
                logger.warning("Ollama health check failed")
            await asyncio.sleep(30)

    async def start(self):
        self._running = True
        logger.info("BatSymphony daemon starting on :%d", self.config.http_port)
        self.memory.append(event_type="lifecycle", data={"action": "start"})

        server_config = uvicorn.Config(
            self.app,
            host=self.config.http_host,
            port=self.config.http_port,
            log_level="info",
        )
        server = uvicorn.Server(server_config)

        await asyncio.gather(
            server.serve(),
            self._git_poll_loop(),
            self._health_check_loop(),
        )

    async def stop(self):
        self._running = False
        self.memory.append(event_type="lifecycle", data={"action": "stop"})
        await self.ollama.close()
        logger.info("BatSymphony daemon stopped")


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    daemon = BatSymphonyDaemon()

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def handle_signal(sig, frame):
        loop.create_task(daemon.stop())

    signal.signal(signal.SIGINT, handle_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_signal)

    try:
        loop.run_until_complete(daemon.start())
    except KeyboardInterrupt:
        loop.run_until_complete(daemon.stop())
    finally:
        loop.close()


if __name__ == "__main__":
    main()
