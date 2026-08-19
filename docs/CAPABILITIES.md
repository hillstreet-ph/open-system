# Capabilities inventory (high level)

Hermes provides skills, plugins, MCP, browser, terminal, code execution, cron, API, dashboard, Telegram.

| Capability | Source | Enabled how | Privilege |
|------------|--------|-------------|-----------|
| Dashboard | hermes_cli web | `HERMES_DASHBOARD` + auth | Admin |
| API server | gateway | `API_SERVER_*` | Secret key |
| Telegram | gateway | `TELEGRAM_*` | Allowlist |
| Skills | `/opt/hermes/skills` + user skills | config | Varies |
| Browser | playwright in image | tools | Isolate per agent |
| Terminal | configured backend | tools | Prefer sandbox, not host |
| MCP | config.yaml / profile | config | Review servers |
| Supabase | optional | env | Server-side service role |

**Installed ≠ Configured ≠ Enabled ≠ Authorized.**

Do not enable all powerful tools for public Telegram agents.
