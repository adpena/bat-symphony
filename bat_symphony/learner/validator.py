"""Validate crystallized skills before deployment."""

from __future__ import annotations

import logging
import time
from typing import Any

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.ollama import OllamaClient

logger = logging.getLogger("bat_symphony.validator")

VALIDATE_PROMPT = """You are validating a crystallized skill. Determine if it is:
1. Well-formed (has clear trigger, implementation guidance, and scope)
2. Non-destructive (won't cause data loss or system harm)
3. Useful (addresses a real recurring pattern)

Skill content:
{skill_content}

Pattern data:
{pattern_data}

Return ONLY valid JSON:
{{"valid": true/false, "reason": "explanation", "confidence": 0.0-1.0}}"""


class Validator:
    def __init__(self, config: Config, memory: MemoryStore, ollama: OllamaClient):
        self.config = config
        self.memory = memory
        self.ollama = ollama

    async def validate_skill(self, skill_content: str, pattern: dict[str, Any]) -> dict[str, Any]:
        """Validate a skill against safety and quality criteria."""
        prompt = VALIDATE_PROMPT.format(
            skill_content=skill_content,
            pattern_data=pattern,
        )

        response = await self.ollama.chat(
            model=self.config.reason_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.1,
        )

        content = response["content"]
        if not content.strip():
            content = response.get("thinking", "")

        result = self._parse_validation(content)
        result["validated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        result["model_used"] = self.config.reason_model

        self.memory.append(event_type="validation", data=result)
        logger.info("Validation result: valid=%s, confidence=%.2f, reason=%s",
                    result.get("valid"), result.get("confidence", 0), result.get("reason", ""))
        return result

    def _parse_validation(self, text: str) -> dict[str, Any]:
        """Parse validation JSON from LLM response."""
        import json

        text = text.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]

        start = text.find("{")
        end = text.rfind("}") + 1
        if start == -1 or end == 0:
            return {"valid": False, "reason": "Could not parse validation response", "confidence": 0.0}

        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            return {"valid": False, "reason": "Invalid JSON in validation response", "confidence": 0.0}
