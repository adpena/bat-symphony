"""Unified telemetry pipeline for cross-project event collection."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from bat_symphony.config import Config

logger = logging.getLogger("bat_symphony.telemetry")


class TelemetryCollector:
    """Collects structured telemetry events from all projects."""

    def __init__(self, config: Config):
        self.config = config
        self._telemetry_dir = config.state_dir / "telemetry"
        self._telemetry_dir.mkdir(parents=True, exist_ok=True)
        self._current_log = self._telemetry_dir / f"events-{time.strftime('%Y%m%d')}.jsonl"

    def emit(
        self,
        source: str,
        event: str,
        data: dict[str, Any] | None = None,
        severity: str = "info",
    ) -> dict[str, Any]:
        """Emit a telemetry event."""
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": source,
            "event": event,
            "severity": severity,
            "data": data or {},
        }
        with open(self._current_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        return entry

    def query(
        self,
        source: str | None = None,
        event: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        days: int = 1,
    ) -> list[dict[str, Any]]:
        """Query telemetry events with optional filters."""
        results = []
        # Scan log files for the requested time window
        for i in range(days):
            ts = time.time() - (i * 86400)
            date_str = time.strftime("%Y%m%d", time.gmtime(ts))
            log_path = self._telemetry_dir / f"events-{date_str}.jsonl"
            if not log_path.exists():
                continue
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if source and entry.get("source") != source:
                        continue
                    if event and entry.get("event") != event:
                        continue
                    if severity and entry.get("severity") != severity:
                        continue
                    results.append(entry)
        return results[-limit:]

    def summary(self, days: int = 1) -> dict[str, Any]:
        """Get telemetry summary: event counts by source and severity."""
        events = self.query(limit=10000, days=days)
        by_source: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_event: dict[str, int] = {}
        for e in events:
            src = e.get("source", "unknown")
            sev = e.get("severity", "info")
            evt = e.get("event", "unknown")
            by_source[src] = by_source.get(src, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_event[evt] = by_event.get(evt, 0) + 1
        return {
            "total_events": len(events),
            "by_source": by_source,
            "by_severity": by_severity,
            "top_events": dict(sorted(by_event.items(), key=lambda x: -x[1])[:10]),
            "days": days,
        }
