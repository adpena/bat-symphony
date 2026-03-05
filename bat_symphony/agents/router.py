"""Route tasks to appropriate agents and models."""

from __future__ import annotations

import logging
from typing import Any

from bat_symphony.agents.base import AgentConfig, create_agent, get_llm_config, run_agent_task
from bat_symphony.agents.builtin import ALL_AGENTS
from bat_symphony.config import Config
from bat_symphony.memory.store import MemoryStore

logger = logging.getLogger("bat_symphony.agents.router")

# Task type to model routing
TASK_MODEL_MAP = {
    "review": "reflect",      # fast model for reviews
    "analyze": "reflect",     # fast model for analysis
    "plan": "reason",         # complex model for planning
    "refine": "reason",       # complex model for refinement
    "code": "reason",         # complex model for code generation
}


class AgentRouter:
    """Route tasks to the right agent with the right model."""

    def __init__(self, config: Config, memory: MemoryStore):
        self.config = config
        self.memory = memory
        self._agents: dict[str, Any] = {}

    def _get_model_for_task(self, task_type: str) -> str:
        """Select model based on task complexity."""
        model_key = TASK_MODEL_MAP.get(task_type, "default")
        if model_key == "reflect":
            return self.config.reflect_model
        elif model_key == "reason":
            return self.config.reason_model
        return self.config.default_model

    def _get_or_create_agent(self, agent_name: str, model_override: str | None = None) -> Any:
        """Get cached agent or create new one."""
        cache_key = f"{agent_name}:{model_override or 'default'}"
        if cache_key not in self._agents:
            agent_cfg = ALL_AGENTS.get(agent_name)
            if not agent_cfg:
                logger.warning("Unknown agent: %s", agent_name)
                return None
            if model_override:
                agent_cfg = AgentConfig(
                    name=agent_cfg.name,
                    description=agent_cfg.description,
                    model=model_override,
                    system_prompt=agent_cfg.system_prompt,
                    tools=agent_cfg.tools,
                )
            self._agents[cache_key] = create_agent(agent_cfg, self.config)
        return self._agents[cache_key]

    async def route(self, agent_name: str, task: str, task_type: str = "default") -> dict[str, Any]:
        """Route a task to the appropriate agent with model selection."""
        model = self._get_model_for_task(task_type)
        agent = self._get_or_create_agent(agent_name, model)

        self.memory.append(event_type="agent_task", data={
            "agent": agent_name,
            "task_type": task_type,
            "model": model,
            "task_preview": task[:200],
        })

        response = await run_agent_task(agent, task)

        self.memory.append(event_type="agent_result", data={
            "agent": agent_name,
            "task_type": task_type,
            "response_length": len(response),
            "success": not response.startswith("Error:"),
        })

        return {
            "agent": agent_name,
            "model": model,
            "response": response,
            "success": not response.startswith("Error:"),
        }

    def list_agents(self) -> list[dict[str, str]]:
        """List all available agents."""
        return [
            {"name": cfg.name, "description": cfg.description}
            for cfg in ALL_AGENTS.values()
        ]
