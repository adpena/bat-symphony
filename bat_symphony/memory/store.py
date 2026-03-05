"""Append-only JSONL interaction log."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


class MemoryStore:
    def __init__(self, state_dir: Path):
        self._dir = state_dir / "memory"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._dir / "interactions.jsonl"

    def append(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": event_type,
            **data,
        }
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read_recent(
        self, limit: int = 50, event_type: str | None = None
    ) -> list[dict[str, Any]]:
        if not self._log_path.exists():
            return []
        entries = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                if event_type and entry.get("type") != event_type:
                    continue
                entries.append(entry)
        return entries[-limit:]

    def count(self, event_type: str | None = None) -> int:
        return len(self.read_recent(limit=999_999, event_type=event_type))
