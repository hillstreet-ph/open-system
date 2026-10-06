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

## Enablement pack (Open-System)

See `deploy/open-system/ENABLEMENT.md` and `scripts/enablement/install-official-skills.sh`.

Curated optional skills for ops/dev (not the full catalog):

- `official/devops/docker-management`
- `official/devops/hermes-s6-container-supervision`
- `official/devops/watchers`
- `official/research/duckduckgo-search`
- `official/research/searxng-search`
- `official/mcp/fastmcp`
- `official/mcp/mcporter`
- `official/web-development/page-agent`

Plugins default-enabled in `deploy/open-system/config.skills-plugins.yaml`:
`disk-cleanup`, `security-guidance`, `memory`, `web/ddgs`, `cron_providers/chronos`.

Full optional catalog: https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog
