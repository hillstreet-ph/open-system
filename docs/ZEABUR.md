# Zeabur deployment (Open-System)

## Services

| Service | Role |
|---------|------|
| hermes-agent | Legacy; keep suspended for rollback |
| hermes-agent-v2 / hermes-agent-docker | Candidate production (Docker image) |

## Image

Prefer digest pin:

```text
kairocasino/open-system@sha256:<digest>
```

Tags: `sha-<short>`, `stable` (after promotion), avoid `:latest` as sole identity.

## Volume

`data` → `/opt/data` (`HERMES_HOME`)

## Ports

| Surface | Port | Env |
|---------|------|-----|
| Dashboard | 9119 | `HERMES_DASHBOARD=true`, basic auth required on `0.0.0.0` |
| API | 8642 | `API_SERVER_ENABLED=true`, `API_SERVER_KEY` (≥16 chars) |

## Health check (critical)

Hermes is slow on first boot. Configure:

- TCP or HTTP on the **published** port
- High failure threshold / long initial delay (minutes, not seconds)

**502 Bad Gateway** almost always means: probe hit a port with nothing listening yet (dashboard refused bind without auth, or API not ready).

## Dashboard auth (required for public bind)

```text
HERMES_DASHBOARD_BASIC_AUTH_USERNAME
HERMES_DASHBOARD_BASIC_AUTH_PASSWORD   # or _PASSWORD_HASH
HERMES_DASHBOARD_BASIC_AUTH_SECRET
```

## Telegram

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_ALLOWED_USERS
HERMES_GATEWAY_BOOTSTRAP_STATE=running
```

## Promotion

Only change production image after staging/smoke. Upstream-sync PRs must **not** auto-deploy production.
