# Zeabur — Open-System / hermes-agent-v2

## Current services (do not destroy)

| Service | Role |
|---------|------|
| `hermes-agent` | **OLD** — keep as rollback. Do not delete volume or backup. |
| `hermes-agent-v2` | **NEW** — target production. Source: `hillstreet-ph/open-system` @ `main`. |
| Gateway | Future production traffic router |

## Volume

- Name: `data` (or as configured)
- Mount: **`/opt/data`**
- Must not be shared writable with the old service simultaneously

## Image strategy (recommended once Docker Hub pipeline is green)

1. Run **Open-System Docker Release** workflow on `main`.
2. Record the published digest from the job summary.
3. On Zeabur service `hermes-agent-v2`, switch from GitHub build to Docker image:
   - Image: `$DOCKERHUB_USERNAME/open-system@sha256:…` (or `:stable` after promotion)
4. Keep ENTRYPOINT/CMD **unset** (use image defaults).
5. Confirm env vars already present on the service (secrets stay in Zeabur; never in git).

## Ports to publish

Align with your env:

- Dashboard: `HERMES_DASHBOARD_PORT` (default **9119**)
- API: `API_SERVER_PORT` (upstream default **8642**; your V2 may use **5000** — match `PORT` / platform web port carefully)

## Health

Use `scripts/healthcheck.sh` logic or platform HTTP checks against dashboard `/` and API `/health` when enabled.
