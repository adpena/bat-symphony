"""Orchestrate the 5-stage self-improvement loop."""

from __future__ import annotations

import logging
from typing import Any

from bat_symphony.config import Config
from bat_symphony.learner.crystallizer import Crystallizer
from bat_symphony.learner.self_writer import SelfWriter
from bat_symphony.learner.validator import Validator
from bat_symphony.memory.reflection import ReflectionEngine
from bat_symphony.memory.store import MemoryStore
from bat_symphony.ollama import OllamaClient

logger = logging.getLogger("bat_symphony.loop")


class LearningLoop:
    def __init__(self, config: Config, memory: MemoryStore, ollama: OllamaClient):
        self.config = config
        self.memory = memory
        self.ollama = ollama
        self.reflection = ReflectionEngine(config, memory, ollama)
        self.crystallizer = Crystallizer(config, memory)
        self.self_writer = SelfWriter(config, memory, ollama)
        self.validator = Validator(config, memory, ollama)
        self._interaction_count = 0

    def should_reflect(self) -> bool:
        """Check if enough interactions have occurred to trigger reflection."""
        self._interaction_count += 1
        return self._interaction_count >= self.config.reflect_every_n

    async def run_cycle(self) -> dict[str, Any]:
        """Execute one full learning cycle: reflect -> crystallize -> write -> validate."""
        result: dict[str, Any] = {
            "patterns_found": 0,
            "skills_crystallized": 0,
            "claude_md_updates": 0,
            "validations_passed": 0,
        }

        # Stage 2: Reflect
        logger.info("Starting reflection cycle")
        patterns = await self.reflection.reflect()
        result["patterns_found"] = len(patterns)

        if not patterns:
            logger.info("No patterns detected, cycle complete")
            self._interaction_count = 0
            return result

        # Stage 3: Crystallize
        ready = self.crystallizer.evaluate_patterns(patterns)

        for candidate in ready:
            skill_path = self.crystallizer.crystallize_skill(candidate)
            skill_content = skill_path.read_text(encoding="utf-8")
            result["skills_crystallized"] += 1

            # Stage 5: Validate
            validation = await self.validator.validate_skill(
                skill_content, candidate.get("pattern", {})
            )

            if validation.get("valid") and validation.get("confidence", 0) >= 0.5:
                result["validations_passed"] += 1

                # Stage 4: Write (CLAUDE.md promotion if threshold met)
                if candidate.get("meets_promote_threshold"):
                    proposal = await self.self_writer.propose_claude_md_update(candidate)
                    if proposal.get("proposed_text"):
                        self.self_writer.apply_claude_md_update(proposal)
                        result["claude_md_updates"] += 1
            else:
                logger.info("Skill '%s' failed validation, keeping as candidate",
                           candidate.get("name"))

        self._interaction_count = 0
        self.memory.append(event_type="learning_cycle", data=result)
        logger.info("Learning cycle complete: %s", result)
        return result
