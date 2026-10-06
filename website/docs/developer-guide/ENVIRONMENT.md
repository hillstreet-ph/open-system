# Environment contract (names only)

Placeholders only in Git. Real values live in Zeabur / GitHub Environments.

## Application (non-secret)

| Name | Purpose |
|------|---------|
| `HERMES_HOME` | Default `/opt/data` |
| `HERMES_DASHBOARD` | Enable dashboard |
| `HERMES_DASHBOARD_HOST` / `_PORT` | Bind (use `0.0.0.0` / `9119` on platforms) |
| `API_SERVER_ENABLED` / `_HOST` / `_PORT` | OpenAI-compatible API |
| `HERMES_GATEWAY_BOOTSTRAP_STATE` | `running` for first-boot gateway |
| `PORT` / `PUBLIC_DOMAIN` | Platform ingress |
| `TELEGRAM_ALLOWED_USERS` | Comma-separated Telegram user IDs |

## Secrets

| Name | Purpose |
|------|---------|
| `API_SERVER_KEY` | API bearer (≥16 chars) |
| `HERMES_DASHBOARD_BASIC_AUTH_*` | Dashboard login |
| `TELEGRAM_BOT_TOKEN` | Bot API |
| `OPENROUTER_API_KEY` / provider keys | Models |
| `SUPABASE_URL` / `SUPABASE_ANON_KEY` | Client-safe Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | **Server only** |
| `DATABASE_URL` | Postgres (server only) |
| `BACKUP_ENCRYPT_KEY` | Backup encryption passphrase |

Never put service-role keys in browser/public clients.
