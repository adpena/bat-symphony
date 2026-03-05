"""Crystallize detected patterns into skills and CLAUDE.md rules."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore

logger = logging.getLogger("bat_symphony.crystallizer")


class Crystallizer:
    def __init__(self, config: Config, memory: MemoryStore):
        self.config = config
        self.memory = memory
        self._candidates_dir = config.state_dir / "learnings"
        self._candidates_dir.mkdir(parents=True, exist_ok=True)
        self._skills_dir = config.state_dir / "skills"
        self._skills_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_patterns(self, patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Evaluate patterns against thresholds, return those ready for crystallization."""
        ready = []
        for p in patterns:
            occurrences = p.get("occurrences", 0)
            success_rate = p.get("success_rate", 0.0)
            name = p.get("name", "unknown")

            # Save as candidate
            candidate = {
                "name": name,
                "pattern": p,
                "evaluated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "meets_skill_threshold": (
                    occurrences >= self.config.skill_threshold_uses
                    and success_rate >= self.config.skill_threshold_success
                ),
                "meets_promote_threshold": (
                    occurrences >= self.config.promote_threshold_uses
                    and success_rate >= self.config.promote_threshold_success
                ),
            }

            candidate_path = self._candidates_dir / f"{name}.json"
            candidate_path.write_text(json.dumps(candidate, indent=2), encoding="utf-8")

            if candidate["meets_skill_threshold"]:
                ready.append(candidate)
                logger.info("Pattern '%s' meets skill threshold (uses=%d, success=%.0f%%)",
                           name, occurrences, success_rate * 100)

        return ready

    def crystallize_skill(self, candidate: dict[str, Any]) -> Path:
        """Write a skill markdown file from a candidate pattern."""
        pattern = candidate["pattern"]
        name = pattern.get("name", "unknown")
        description = pattern.get("description", "No description")
        suggested = pattern.get("suggested_skill", description)
        category = pattern.get("category", "general")

        skill_content = f"""# Skill: {name}

**Category:** {category}
**Crystallized:** {time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())}
**Occurrences:** {pattern.get("occurrences", 0)}
**Success Rate:** {pattern.get("success_rate", 0):.0%}

## Description

{description}

## When to Use

{suggested}

## Implementation

(Auto-generated from pattern detection. Refine through usage.)
"""
        skill_path = self._skills_dir / f"{name}.md"
        skill_path.write_text(skill_content, encoding="utf-8")

        self.memory.append(event_type="crystallization", data={
            "skill_name": name,
            "path": str(skill_path),
            "pattern": pattern,
        })

        logger.info("Crystallized skill: %s -> %s", name, skill_path)
        return skill_path

    def get_candidates(self) -> list[dict[str, Any]]:
        """Return all current candidates."""
        candidates = []
        for p in sorted(self._candidates_dir.glob("*.json")):
            try:
                candidates.append(json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                continue
        return candidates

    def get_skills(self) -> list[dict[str, str]]:
        """Return all crystallized skills."""
        return [
            {"name": p.stem, "path": str(p), "content": p.read_text(encoding="utf-8")}
            for p in sorted(self._skills_dir.glob("*.md"))
        ]
