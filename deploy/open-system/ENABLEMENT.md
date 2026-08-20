# Enable skills, plugins, tools (production)

References:
- https://hermes-agent.org/
- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://hermes-agent.nousresearch.com/docs/user-guide/features/skills
- https://hermes-agent.nousresearch.com/docs/reference/optional-skills-catalog
- https://hermesatlas.com/lists/

## Design rule

**Installed ≠ Enabled ≠ Authorized.**

Public / Telegram agents stay on least privilege. Full skill catalogs are for
`ops-agent` / `dev-agent` / admin profiles, not unrestricted public groups.

## Bundled skills

The Docker image already seeds **bundled** skills under the profile when first
started (unless `.no-bundled-skills` is present). No action required for those.

## Optional skills (official)

Inside the running container (Zeabur → hermes-agent → Command / shell):

```bash
export HERMES_HOME=/opt/data
# If repo is not mounted, copy scripts from GitHub or paste commands:
hermes skills install official/devops/docker-management
hermes skills install official/devops/hermes-s6-container-supervision
hermes skills install official/devops/watchers
hermes skills install official/research/duckduckgo-search
hermes skills install official/research/searxng-search
hermes skills install official/mcp/fastmcp
```

Or run the curated script from the repo checkout:
`scripts/enablement/install-official-skills.sh`

## Plugins

Edit `$HERMES_HOME/config.yaml`:

```yaml
plugins:
  enabled:
    - disk-cleanup
    - security-guidance
    - memory
    - web/ddgs
    - cron_providers/chronos
```

Or: `hermes plugins enable disk-cleanup` (etc.)

## Tools (agent loop)

Built-in tools (web, memory, code, browser, terminal) are part of the agent loop
(`run_agent.py`). Control exposure via:

- Profile permission (see `deploy/open-system/profiles/`)
- Platform skill toggles: `hermes skills` TUI
- `TELEGRAM_ALLOWED_USERS` + group routes in Supabase

## After changes

Restart the Zeabur service so gateway reloads config and skills index.
