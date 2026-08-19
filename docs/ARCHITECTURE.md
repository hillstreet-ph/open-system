# Open-System architecture

## Principle

**CODE ≠ DATA ≠ SECRETS**

| Layer | Store | Disposable? |
|-------|--------|-------------|
| Application code | GitHub `hillstreet-ph/open-system` + Docker Hub image | Yes |
| Runtime process | Zeabur / any Docker host | Yes |
| Hermes state | Volume `/opt/data` (`HERMES_HOME`) | **No** |
| Structured DB / Auth / Storage | Supabase (optional control plane) | **No** (separate backups) |
| Secrets | GitHub Actions secrets + Zeabur env | Never in Git |

## Promotion flow

```
NousResearch/hermes-agent
        → upstream-sync/* (PR only, never auto-merge to main)
        → CI
        → main
        → Docker multi-arch image (sha + digest)
        → staging verification (manual/workflow)
        → production pin @sha256:DIGEST
```

## Services

- **Hermes Agent** (s6-overlay): gateway, dashboard, API, tools
- **Telegram**: via `TELEGRAM_BOT_TOKEN` + allowlists
- **OpenAI-compatible API**: `API_SERVER_*` (default port 8642)
- **Dashboard**: port 9119; requires auth provider on non-loopback binds

## Persistence

See [PERSISTENCE.md](./PERSISTENCE.md). Primary contract: **`/opt/data`**.

## Open-System additions (preserve on upstream sync)

- `.github/workflows/docker-release.yml`
- `.github/workflows/upstream-sync.yml`
- `.github/workflows/staging-smoke.yml` (when present)
- `scripts/backup/*`, `scripts/restore/*`, `scripts/status.sh`
- `deploy/zeabur/*`, `docs/*` ops docs
