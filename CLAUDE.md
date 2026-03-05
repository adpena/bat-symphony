# CLAUDE.md

BatSymphony: self-improving agentic system on BAT00 (Windows).

## Architecture
- Python asyncio daemon managed by uv
- Ollama for local inference (qwen3.5 models on localhost:11434)
- FastAPI HTTP server on :8787
- State in E:\BatSymphony\bat-symphony\state\

## Commands
```bash
uv run python -m bat_symphony          # Start daemon
uv run pytest -v                       # Run tests
curl http://localhost:8787/health      # Health check
powershell -File scripts\daemon.ps1 start   # Managed start
powershell -File scripts\daemon.ps1 stop    # Managed stop
powershell -File scripts\daemon.ps1 status  # Check status
powershell -File scripts\doctor.ps1         # Stack health
```

## Model Routing
- qwen3.5:9b: fast reflection, pattern detection, simple tasks
- qwen3.5:27b: complex reasoning, code review, design
- qwen3.5:35b-a3b: specialized tasks, long context

## Conventions
- All state in state/ (gitignored)
- Secrets in .env only
- Self-modifications go through Git branches
- JSONL for interaction logs
- Skills as Markdown in .claude/skills/
- Tests required for all new modules (pytest)

## Qwen-Agent Integration
- Qwen-Agent SDK available for building MCP-compatible tool-using agents
- Install: `uv add qwen-agent`
- Use for: structured tool calls, multi-step reasoning, browser automation
- Reference: https://github.com/QwenLM/Qwen-Agent
