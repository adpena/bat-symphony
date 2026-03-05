"""Central configuration with env-var overrides."""

from __future__ import annotations

import os
from pathlib import Path


class Config:
    def __init__(self):
        self.ollama_url: str = os.getenv("BAT_OLLAMA_URL", "http://localhost:11434")
        self.http_port: int = int(os.getenv("BAT_HTTP_PORT", "8787"))
        self.http_host: str = os.getenv("BAT_HTTP_HOST", "0.0.0.0")

        self.state_dir: Path = Path(
            os.getenv("BAT_STATE_DIR", str(Path(__file__).resolve().parent.parent / "state"))
        )

        # Model routing
        self.default_model: str = os.getenv("BAT_DEFAULT_MODEL", "qwen3.5:9b")
        self.reflect_model: str = os.getenv("BAT_REFLECT_MODEL", "qwen3.5:9b")
        self.reason_model: str = os.getenv("BAT_REASON_MODEL", "qwen3.5:27b")

        # Learning loop tunables
        self.reflect_every_n: int = int(os.getenv("BAT_REFLECT_EVERY_N", "10"))
        self.skill_threshold_uses: int = int(os.getenv("BAT_SKILL_THRESHOLD_USES", "2"))
        self.skill_threshold_success: float = float(os.getenv("BAT_SKILL_THRESHOLD_SUCCESS", "0.5"))
        self.promote_threshold_uses: int = int(os.getenv("BAT_PROMOTE_THRESHOLD_USES", "3"))
        self.promote_threshold_success: float = float(os.getenv("BAT_PROMOTE_THRESHOLD_SUCCESS", "0.7"))

        # Git watcher
        self.watch_repos: list[str] = [
            r for r in os.getenv("BAT_WATCH_REPOS", "").split(",") if r.strip()
        ]
        self.git_poll_interval_s: int = int(os.getenv("BAT_GIT_POLL_INTERVAL_S", "60"))

        # Mac bridge
        self.mac_host: str = os.getenv("BAT_MAC_HOST", "192.168.1.170")
        self.mac_ssh_user: str = os.getenv("BAT_MAC_SSH_USER", "adpena")
