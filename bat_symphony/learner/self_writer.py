"""Generate self-modifications: CLAUDE.md diffs and skill files."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore
from bat_symphony.ollama import OllamaClient

logger = logging.getLogger("bat_symphony.self_writer")

CLAUDE_MD_PROMPT = """You are a self-improving agent. Based on this learning, propose a concise addition to CLAUDE.md.

Learning:
{learning}

Current CLAUDE.md:
{current_claude_md}

Rules:
- Add ONLY the new section/rule. Do not rewrite existing content.
- Keep it under 5 lines.
- Use markdown format.
- Return ONLY the new text to append (no explanation).
"""


class SelfWriter:
    def __init__(self, config: Config, memory: MemoryStore, ollama: OllamaClient):
        self.config = config
        self.memory = memory
        self.ollama = ollama
        self._repo_root = config.state_dir.parent
        self._claude_md_path = self._repo_root / "CLAUDE.md"

    async def propose_claude_md_update(self, candidate: dict[str, Any]) -> dict[str, Any]:
        """Generate a proposed CLAUDE.md addition from a promoted pattern."""
        current = ""
        if self._claude_md_path.exists():
            current = self._claude_md_path.read_text(encoding="utf-8")

        prompt = CLAUDE_MD_PROMPT.format(
            learning=candidate.get("pattern", {}),
            current_claude_md=current[:2000],
        )

        response = await self.ollama.chat(
            model=self.config.reason_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512,
            temperature=0.2,
        )

        content = response["content"]
        if not content.strip():
            content = response.get("thinking", "")

        proposal = {
            "type": "claude_md_update",
            "candidate_name": candidate.get("name", "unknown"),
            "proposed_text": content.strip(),
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "model_used": self.config.reason_model,
        }

        self.memory.append(event_type="self_write_proposal", data=proposal)
        logger.info("Proposed CLAUDE.md update for pattern: %s", candidate.get("name"))
        return proposal

    def apply_claude_md_update(self, proposal: dict[str, Any]) -> bool:
        """Append the proposed text to CLAUDE.md."""
        text = proposal.get("proposed_text", "").strip()
        if not text:
            logger.warning("Empty proposal, skipping")
            return False

        current = ""
        if self._claude_md_path.exists():
            current = self._claude_md_path.read_text(encoding="utf-8")

        updated = current.rstrip() + "\n\n" + text + "\n"
        self._claude_md_path.write_text(updated, encoding="utf-8")

        self.memory.append(event_type="self_write_applied", data={
            "path": str(self._claude_md_path),
            "candidate_name": proposal.get("candidate_name"),
        })
        logger.info("Applied CLAUDE.md update: %s", proposal.get("candidate_name"))
        return True
