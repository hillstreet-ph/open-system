# Production enablement (Open-System)

Professional production posture: **enable by need**, not “turn everything on”.

## Already automated (main)

- Upstream sync via PR (`upstream-sync.yml`)
- Docker multi-arch release (`docker-release.yml`)
- Staging smoke (`staging-smoke.yml`)
- Backup schedules + Supabase sync (`backup-scheduled.yml`, `github-supabase-sync.yml`)
- Supabase migrations (`supabase-migrate.yml`)
- Ops docs: ARCHITECTURE, BACKUP, DR, ZEABUR, INTEGRATION, TELEGRAM, CAPABILITIES

## Feature layers

| Layer | How to enable | Risk |
|-------|----------------|------|
| Dashboard | `HERMES_DASHBOARD=true` + basic auth env | Medium |
| API | `API_SERVER_*` | Medium |
| Telegram | `TELEGRAM_BOT_TOKEN` + allowlist | Medium |
| Multi-agent profiles | `deploy/open-system/profiles/*` on volume | Low |
| Skills (bundled) | Already in image; user skills under `/opt/data` | Varies |
| Optional skills | Install selectively from `optional-skills/` | Varies |
| Plugins | Trust allowlist only | High if misconfigured |
| Browser | Needs memory ≥2–4GB | High RAM |
| Terminal | Prefer docker sandbox, never public | Critical |
| Memory | Native under `HERMES_HOME` | Low |
| Supabase control plane | Migrations + service role server-side | Medium |
| Knowledge / RAG | Product phase (pgvector tables optional) | Medium |

## Telegram multi-agent (groups)

See `deploy/open-system/telegram/routes.example.yaml` and `docs/TELEGRAM.md`.

1. One bot token
2. Multiple groups → different `agent_profile`
3. Allowlist human admins
4. Public groups → `public-agent` only

## Zeabur production checklist

1. Image pin: `kairocasino/open-system@sha256:…` or `sha-<git>`
2. Domain → port 9119
3. Memory ≥1536 MiB (prefer 4GB node)
4. Single volume `/opt/data`
5. Env: dashboard auth, API key, Telegram, OpenRouter
6. Backup: volume script + Supabase `pg_dump` schedule

## What “complete” does not mean

- Not every optional skill/plugin installed by default
- Not unrestricted shell for all agents
- Not free model API keys shipped in Git
- Not auto-merge upstream to production without CI

Least privilege is the professional standard for a production agent platform.
