# Persistence inventory (Open-System / Hermes)

Default volume: **`HERMES_HOME=/opt/data`** (Zeabur: mount `data` → `/opt/data`).

| Path (under HERMES_HOME) | Class | Backup? | Notes |
|--------------------------|--------|---------|--------|
| `config.yaml` | PERSISTENT | YES | Core config; migration-sensitive |
| `.env` | SECRET | optional encrypted | Prefer platform secrets over file |
| `auth.json` / OAuth tokens | SECRET | YES encrypted | |
| `gateway_state.json` | PERSISTENT | YES | Gateway supervised state |
| `state.db` / SQLite | PERSISTENT | YES | Sessions/state |
| `sessions/`, transcripts | PERSISTENT | YES | |
| `skills/` (user-installed) | PERSISTENT | YES | Bundled skills regeneratable |
| `plugins/` config | PERSISTENT | YES | |
| MCP server configs | PERSISTENT | YES | |
| cron job definitions | PERSISTENT | YES | |
| `logs/` | EPHEMERAL | optional | Usually exclude large logs |
| browser/playwright caches | REGENERATABLE | NO | Exclude from backup |
| `__pycache__` | EPHEMERAL | NO | |

## Zeabur

- Volume id `data` → `/opt/data`
- Never delete volume for ordinary image upgrades
- Application containers are disposable; volume is not

## Classification summary

- **EPHEMERAL**: caches, logs (unless retention policy says otherwise)
- **PERSISTENT**: config, sessions, skills, gateway state, DBs under `/opt/data`
- **SECRET**: tokens, keys — store in platform secret stores; backup only if encrypted
- **BACKUP_REQUIRED**: all PERSISTENT + SECRET (encrypted)
- **REGENERATABLE**: playwright browsers, pip caches, bundled skills sync
