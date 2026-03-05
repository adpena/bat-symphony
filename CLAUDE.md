# CLAUDE.md

BatSymphony: self-improving agentic system on BAT00 (Windows, 192.168.1.216).
Integrated with Vertigo and Molt symphonies on Mac (192.168.1.170).

## Architecture
- Python asyncio daemon managed by uv
- Ollama for local inference (qwen3.5 models on localhost:11434)
- Qwen-Agent SDK for tool-using agents
- FastAPI HTTP server on :8787
- State in E:\BatSymphony\bat-symphony\state\
- Connected to Mac via HTTP + Git + SSH

## Commands
```bash
uv run python -m bat_symphony          # Start daemon
uv run pytest -v                       # Run tests
curl http://localhost:8787/health      # Health check
powershell -File scripts\daemon.ps1 start     # Managed start
powershell -File scripts\daemon.ps1 stop      # Managed stop
powershell -File scripts\daemon.ps1 restart   # Restart
powershell -File scripts\daemon.ps1 status    # Check status
powershell -File scripts\daemon.ps1 logs      # Tail logs
powershell -File scripts\doctor.ps1           # Stack health
```

## HTTP API
- `GET  /health` — status, uptime, model info
- `GET  /skills` — crystallized skills
- `GET  /learnings` — pattern detection candidates
- `GET  /agents` — available Qwen-Agent agents
- `POST /agents/{name}/run` — run task through agent
- `POST /trigger` — force learning cycle
- `POST /memory` — query interaction memory
- `POST /bus/publish` — publish to agent bus
- `GET  /bus/channels` — list bus channels
- `POST /telemetry/emit` — emit telemetry event
- `GET  /telemetry/summary` — telemetry dashboard
- `POST /shared/store` — store shared knowledge
- `GET  /shared/retrieve` — retrieve shared knowledge

## Model Routing
- qwen3.5:9b: fast reflection, pattern detection, simple tasks
- qwen3.5:27b: complex reasoning, code review, design
- qwen3.5:35b-a3b: specialized tasks, long context

## Self-Improvement Loop
Five-stage continuous learning:
1. **Observe** — log all interactions as JSONL
2. **Reflect** — Ollama analyzes logs for patterns (every N interactions)
3. **Crystallize** — promote patterns to skills (threshold: 2+ uses, 50%+ success)
4. **Write** — generate skill files and CLAUDE.md updates
5. **Validate** — sandbox test before deploy

## Qwen-Agent Agents
Built-in agents powered by local Ollama:
- `code_reviewer` — code quality analysis
- `commit_analyzer` — git change summarization
- `skill_refiner` — improve crystallized skills
- `task_planner` — break tickets into steps

## Conventions
- All state in state/ (gitignored)
- Secrets in .env only (chmod 600)
- Self-modifications go through Git branches
- JSONL for interaction logs
- Skills as Markdown in state/skills/
- Tests required for all new modules (pytest)
- Telemetry events written to state/telemetry/

## Cross-Machine Communication
- Agent bus: local channels + remote bridge to Mac Symphony
- Shared memory: federated knowledge store (BAT00 ↔ Mac)
- Telemetry: unified event pipeline across all projects
- Git: push/pull for durable state synchronization
