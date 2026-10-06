# Open-System Production Architecture

Portable production model for Hermes Agent under the Open-System deployment.

## Identity

| Layer | Value |
|-------|-------|
| Source of truth | `hillstreet-ph/open-system` (GitHub) |
| Upstream | `NousResearch/hermes-agent` |
| Image registry | Docker Hub (`$DOCKERHUB_USERNAME/open-system`) |
| Current runtime | Zeabur (`hermes-agent-v2`) |
| Persistent state | `/opt/data` volume |
| Immutable code | `/opt/hermes` (from image) |

## Critical safety rules

1. **Never delete** the old Zeabur service `hermes-agent` or its volume/backup until V2 is proven and a rollback window has passed.
2. **Never attach** the same writable `/opt/data` volume to old and new containers at the same time.
3. **Do not override** Docker `ENTRYPOINT` or `CMD` unless source inspection proves it is required. The image uses `entrypoint-dispatch.sh` + s6-overlay.
4. **Never** commit secrets. Use GitHub Actions secrets + Zeabur service variables only.
5. Prefer image **digest** (or `:stable`) over `:latest` for production.

## Ports (verified from upstream Hermes)

| Service | Default port | Notes |
|---------|--------------|-------|
| Dashboard | **9119** | `HERMES_DASHBOARD=true`, bind `0.0.0.0` on platforms |
| API server | **8642** | `API_SERVER_ENABLED=true` + `API_SERVER_KEY` required. Your Zeabur V2 may override via `API_SERVER_PORT` (e.g. 5000) — keep env consistent with published ports. |

## Environment contract (Open-System / Zeabur)

See root `.env.example` section **OPEN-SYSTEM / ZEABUR PRODUCTION CONTRACT**.

Classification:

| Variable class | Examples |
|----------------|----------|
| PUBLIC CONFIG | `API_SERVER_ENABLED`, `API_SERVER_HOST`, `API_SERVER_PORT`, `HERMES_DASHBOARD`, `PUBLIC_DOMAIN` |
| SERVER-ONLY SECRET | `API_SERVER_KEY`, `PASSWORD`, `HERMES_DASHBOARD_BASIC_AUTH_*`, `AI_HUB_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY` |
| OPTIONAL | Supabase URL/anon, messaging platform tokens |
| RUNTIME | All of the above — never bake into image layers |

## CI/CD flow

```
NousResearch/hermes-agent
        ↓ (upstream-sync.yml → PR only)
hillstreet-ph/open-system main
        ↓ (docker-release.yml)
Docker Hub :sha-… / :latest / :stable
        ↓ (manual promote)
Zeabur hermes-agent-v2  +  /opt/data volume
```

## Cutover checklist

- [ ] Image built and pushed (digest recorded)
- [ ] V2 healthcheck green
- [ ] Dashboard + API authenticated
- [ ] Sessions / skills / memory verified
- [ ] Backup of `/opt/data` taken and checksum verified
- [ ] Gateway routes production domain to V2
- [ ] Old `hermes-agent` suspended but retained for rollback window

## Rollback

1. **App only:** point Zeabur at previous image digest.
2. **App + data:** previous digest + restore verified archive via `scripts/restore.sh`.
3. Keep old service available until confidence window ends.

## Disaster recovery (portable)

1. Provision any Docker host
2. `docker pull <image>@sha256:…`
3. Create volume mounted at `/opt/data`
4. `scripts/restore.sh backup.tar.gz /opt/data`
5. Inject secrets (env file / platform secrets)
6. Start container (do not override ENTRYPOINT)
7. `scripts/healthcheck.sh` / `scripts/verify-deployment.sh`

## Related Open-System ops docs

- [ARCHITECTURE.md](./ARCHITECTURE.md)
- [DEPLOYMENT.md](./DEPLOYMENT.md)
- [ZEABUR.md](./ZEABUR.md)
- [PERSISTENCE.md](./PERSISTENCE.md)
- [BACKUP.md](./BACKUP.md)
- [DISASTER-RECOVERY.md](./DISASTER-RECOVERY.md)
- [UPSTREAM-SYNC.md](./UPSTREAM-SYNC.md)
- [ENVIRONMENT.md](./ENVIRONMENT.md)
- [TELEGRAM.md](./TELEGRAM.md)
- [SUPABASE.md](./SUPABASE.md)
- [SECURITY.md](./SECURITY.md)
- [RUNBOOK.md](./RUNBOOK.md)
