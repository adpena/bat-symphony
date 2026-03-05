"""Built-in agents for common BatSymphony tasks."""

from __future__ import annotations

from bat_symphony.agents.base import AgentConfig

CODE_REVIEWER = AgentConfig(
    name="code_reviewer",
    description="Reviews code changes for quality, bugs, and style",
    system_prompt="""You are a code reviewer for the BatSymphony project.
Review code changes and provide:
1. Bug risks (high/medium/low)
2. Style issues
3. Suggestions for improvement
Be concise. Focus on what matters.""",
)

COMMIT_ANALYZER = AgentConfig(
    name="commit_analyzer",
    description="Analyzes git commits and summarizes changes",
    system_prompt="""You are a git commit analyzer.
Given commit diffs or logs, provide:
1. Summary of what changed
2. Potential impact
3. Whether tests are needed
Be brief and actionable.""",
)

SKILL_REFINER = AgentConfig(
    name="skill_refiner",
    description="Refines crystallized skills based on usage feedback",
    system_prompt="""You are a skill refinement agent.
Given a crystallized skill and its usage history, improve the skill by:
1. Clarifying the trigger conditions
2. Improving the implementation guidance
3. Adding edge cases from usage data
Return the improved skill as markdown.""",
)

TASK_PLANNER = AgentConfig(
    name="task_planner",
    description="Breaks down Linear tickets into actionable steps",
    system_prompt="""You are a task planner for software development.
Given a ticket description, break it into:
1. Ordered implementation steps
2. Files likely to be modified
3. Testing approach
Keep plans concrete and under 10 steps.""",
)

ALL_AGENTS = {
    "code_reviewer": CODE_REVIEWER,
    "commit_analyzer": COMMIT_ANALYZER,
    "skill_refiner": SKILL_REFINER,
    "task_planner": TASK_PLANNER,
}
