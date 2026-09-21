# CLAUDE.md — Open-System

> AI agent collaboration guide for the Open-System project.

## Project Identity

- **Name**: Open-System
- **Role**: Execution Plane — Agent orchestration, task execution, workflow engine
- **Language**: Python
- **Organization**: hillstreet-ph
- **Repository**: [github.com/hillstreet-ph/open-system](https://github.com/hillstreet-ph/open-system)

## Architecture Position

Open-System is the **execution plane** of the HillStreet open-platform stack. It receives instructions from Open-Connect (control plane) and stores artifacts via Open-Box (data plane).

```
[Open-Connect] → [Open-System (this)] → [Open-Box]
                       ↕
              [Agent Workers / Zeabur]
              [Telegram Routes]
              [Knowledge Collections]
```

### Sister Projects

| Project | Role | Supabase | Relationship |
|---------|------|----------|-------------|
| open-connect | Control plane | huadtiuuoiriqrjpjxhr | Sends execution requests |
| **open-system** | Execution plane | huadtiuuoiriqrjpjxhr | This repo — executes tasks |
| open-box | Data plane | huadtiuuoiriqrjpjxhr | Stores execution artifacts |
| open-tgate | Telegram gateway | hoseohvgoiarxluxqwqv | Telegram session bridge |
| open-teleset | Comms server | hoseohvgoiarxluxqwqv | Multi-account Telegram |

## Infrastructure Stack

| Layer | Service | Details |
|-------|---------|---------|
| Source | GitHub | hillstreet-ph/open-system, branch: main |
| Database | Supabase | Project: huadtiuuoiriqrjpjxhr, Schema: open_system + public |
| Container | Docker Hub | hillstreet/open-system |
| Runtime | Zeabur | Project: open-system-project (services: hermes-agent, app-gateway, hermes-agent-recovery) |
| Edge | Cloudflare | TBD |
| Monitoring | Sentry | TBD |

## Database Schema

### Public schema (prefixed tables — existing production data)
- `open_system_agents` — registered agent definitions (5 rows)
- `open_system_deployments` — deployment records (3 rows)
- `open_system_sync_events` — synchronization events (4 rows)
- `open_system_backup_catalog` — backup metadata
- `open_system_telegram_routes` — Telegram message routing rules
- `open_system_audit_events` — audit trail
- `open_system_system_settings` — system configuration
- `open_system_knowledge_collections` — knowledge base collections
- `open_system_knowledge_documents` — knowledge documents
- `open_system_agent_teams` — agent team compositions
- `open_system_mcp_connections` — MCP server connections

### open_system schema (new project-specific tables)
- `workflows` — workflow definitions (sequential/parallel/conditional/loop)
- `task_executions` — individual task execution records with status tracking
- `execution_logs` — structured execution logs (debug/info/warn/error/fatal)

## Zeabur Services

The project runs 3 services on Zeabur:
1. **hermes-agent** — primary agent worker
2. **app-gateway** — API gateway
3. **hermes-agent-recovery** — agent recovery/resilience service

## Key Concepts

- **Agents**: Autonomous workers that execute tasks. Defined in `open_system_agents`.
- **Workflows**: Multi-step execution plans (sequential, parallel, conditional, loop).
- **Telegram Routes**: Message routing rules connecting Telegram chats to agents.
- **Knowledge Collections**: Document collections for agent context/RAG.

## Development Workflow

```
feature/* → development → PR → main → Docker build → Docker Hub → Zeabur deploy
```

## Important Rules for AI Agents

1. **Production data exists** — 5 agents, 3 deployments, 4 sync events are live
2. **Schema isolation** — use `open_system` schema for new tables, `public.open_system_*` for existing
3. **Never delete agents or deployments** without explicit authorization
4. **Telegram routes** connect to open-tgate/open-teleset — coordinate changes
5. **Health checks** — verify agent liveness after any deployment
6. **Recovery service** — hermes-agent-recovery must survive agent restarts
7. **Python conventions** — follow existing code style, use type hints

## Quick Start for New AI Agents

1. Read this file and check `deploy/docs/GITHUB_SECRETS_REQUIREMENTS.md`
2. Inspect existing agents: `SELECT * FROM public.open_system_agents`
3. Check Zeabur service status before making changes
4. Review `open_system_telegram_routes` for active message routing
5. New tables go in the `open_system` schema with RLS enabled
6. Test agent connectivity after any infrastructure change
