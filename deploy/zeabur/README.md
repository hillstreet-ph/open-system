# Zeabur — Open-System / hermes-agent-v2

## Services (do not destroy old until V2 verified)

| Service | Role |
|---------|------|
| `hermes-agent` | **OLD** — keep as rollback. Do not delete volume or backup. |
| `hermes-agent-v2` | **NEW** — candidate production. Source or Docker image from this repo. |
| Gateway | Future production traffic router |

## Volume

- Mount path: **`/opt/data`** (Hermes `HERMES_HOME` / persistent state)
- Must not be shared writable with the old service simultaneously
- Image code lives under `/opt/hermes` (immutable)

## Image

Prefer immutable digest after **Open-System Docker Release** succeeds:

```text
kairocasino/open-system@sha256:<digest>
```

Or tags: `:sha-<short>`, `:stable` (after promotion), avoid relying only on `:latest`.

Leave **ENTRYPOINT / CMD empty** on Zeabur (use image defaults: `entrypoint-dispatch.sh` + s6).

## Networking (canonical from Hermes source)

| Surface | Default port | Env |
|---------|--------------|-----|
| Dashboard (UI) | **9119** | `HERMES_DASHBOARD=true`, `HERMES_DASHBOARD_HOST=0.0.0.0`, `HERMES_DASHBOARD_PORT` |
| API server (OpenAI-compatible) | **8642** | `API_SERVER_ENABLED=true`, `API_SERVER_HOST=0.0.0.0`, `API_SERVER_PORT`, `API_SERVER_KEY` (required) |

Zeabur platform `PORT` is the public ingress mapping — map it to the surface you expose (usually dashboard 9119, or API 8642). If you previously used 5000/8080, treat those as **overrides** via `API_SERVER_PORT` / `HERMES_DASHBOARD_PORT` and keep published ports consistent.

## Required runtime variable *names* (values only in Zeabur UI)

**Non-secret:** `API_SERVER_ENABLED`, `API_SERVER_HOST`, `API_SERVER_PORT`, `HERMES_DASHBOARD`, `HERMES_DASHBOARD_BASIC_AUTH_USERNAME`, `PUBLIC_DOMAIN`, `PORT`

**Secret:** `API_SERVER_KEY`, `PASSWORD` (if used as shared source), `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`, `HERMES_DASHBOARD_BASIC_AUTH_SECRET`, provider API keys, `AI_HUB_API_KEY`

Optional Supabase (control plane only unless app code uses it): `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` (server-only), `DATABASE_URL`

## Health

After deploy: `scripts/healthcheck.sh` / `scripts/verify-deployment.sh`  
Probe dashboard `/` on 9119 and API `/health` or `/v1/models` (with Bearer key) on the configured API port.
