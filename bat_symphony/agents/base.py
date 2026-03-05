"""Base agent using Qwen-Agent SDK with local Ollama backend."""

from __future__ import annotations

import logging
from typing import Any

from bat_symphony.config import Config

logger = logging.getLogger("bat_symphony.agents")


class AgentConfig:
    """Configuration for a Qwen-Agent instance."""

    def __init__(
        self,
        name: str,
        description: str,
        model: str | None = None,
        system_prompt: str = "",
        tools: list[str] | None = None,
    ):
        self.name = name
        self.description = description
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or []


def get_llm_config(config: Config, model: str | None = None) -> dict[str, Any]:
    """Build Qwen-Agent compatible LLM config pointing to local Ollama."""
    return {
        "model": model or config.default_model,
        "model_server": config.ollama_url + "/v1",
        "api_key": "ollama",
        "generate_cfg": {
            "max_input_tokens": 8192,
            "max_retries": 2,
        },
    }


def create_agent(agent_config: AgentConfig, app_config: Config) -> Any:
    """Create a Qwen-Agent Assistant instance.

    Returns the agent, or None if qwen-agent is not installed.
    """
    try:
        from qwen_agent.agent import Agent as QwenAgent
        from qwen_agent.agents import Assistant
    except ImportError:
        logger.warning("qwen-agent not installed. Install with: uv add qwen-agent")
        return None

    llm_cfg = get_llm_config(app_config, agent_config.model)

    agent = Assistant(
        llm=llm_cfg,
        name=agent_config.name,
        description=agent_config.description,
        system_message=agent_config.system_prompt,
        function_list=agent_config.tools if agent_config.tools else None,
    )
    logger.info("Created Qwen-Agent: %s (model=%s)", agent_config.name, llm_cfg["model"])
    return agent


async def run_agent_task(agent: Any, task: str) -> str:
    """Run a task through a Qwen-Agent and return the text response.

    Handles both sync and async agent.run() patterns.
    """
    if agent is None:
        return "Error: agent not available (qwen-agent not installed)"

    messages = [{"role": "user", "content": task}]

    try:
        # Qwen-Agent's run() returns a generator of message lists
        response_text = ""
        for responses in agent.run(messages=messages):
            if responses:
                last = responses[-1]
                if isinstance(last, dict):
                    response_text = last.get("content", "")
                elif hasattr(last, "content"):
                    response_text = last.content or ""
        return response_text
    except Exception as e:
        logger.exception("Agent task failed: %s", e)
        return f"Error: {e}"
