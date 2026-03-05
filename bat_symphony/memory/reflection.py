"""Analyze interaction logs to detect recurring patterns."""

from __future__ import annotations

import json
import logging
from typing import Any

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.ollama import OllamaClient

logger = logging.getLogger("bat_symphony.reflection")

REFLECT_PROMPT = """Analyze these recent interaction logs and identify recurring patterns.

For each pattern found, provide:
- name: short snake_case identifier
- description: what the pattern is
- occurrences: how many times you see it
- success_rate: estimated success rate (0.0-1.0)
- category: one of [tool_usage, file_path, prompt_template, error_recovery, workflow]
- suggested_skill: brief description of a skill that could be crystallized from this

Return ONLY valid JSON: {"patterns": [...]}
If no patterns found, return: {"patterns": []}

Logs:
{logs}"""


class ReflectionEngine:
    def __init__(self, config: Config, memory: MemoryStore, ollama: OllamaClient):
        self.config = config
        self.memory = memory
        self.ollama = ollama

    async def reflect(self) -> list[dict[str, Any]]:
        """Analyze recent interactions and return detected patterns."""
        recent = self.memory.read_recent(limit=self.config.reflect_every_n * 2)
        if len(recent) < self.config.reflect_every_n:
            logger.info("Not enough interactions for reflection (%d < %d)", len(recent), self.config.reflect_every_n)
            return []

        logs_text = "\n".join(json.dumps(e, default=str) for e in recent[-self.config.reflect_every_n:])
        prompt = REFLECT_PROMPT.format(logs=logs_text)

        response = await self.ollama.chat(
            model=self.config.reflect_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.3,
        )

        content = response["content"]
        if not content.strip():
            content = response.get("thinking", "")

        # Extract JSON from response
        patterns = self._parse_patterns(content)

        for p in patterns:
            self.memory.append(event_type="reflection", data={"pattern": p})
            logger.info("Detected pattern: %s (occurrences=%s, success=%.0f%%)",
                       p.get("name"), p.get("occurrences"), (p.get("success_rate", 0) * 100))

        return patterns

    def _parse_patterns(self, text: str) -> list[dict[str, Any]]:
        """Extract patterns JSON from LLM response, handling markdown fences."""
        text = text.strip()
        # Strip markdown code fences
        if "```json" in text:
            text = text.split("```json", 1)[1]
            text = text.split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1]
            text = text.split("```", 1)[0]

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            logger.warning("No JSON found in reflection response")
            return []

        try:
            data = json.loads(text[start:end])
            return data.get("patterns", [])
        except json.JSONDecodeError as e:
            logger.warning("Failed to parse reflection JSON: %s", e)
            return []
