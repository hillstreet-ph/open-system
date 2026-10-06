# Hermes /opt/data Persistence Manifest

Volume mount path: **`/opt/data`**  
Treat as the only mutable runtime state. Image code lives under `/opt/hermes` and must remain immutable.

| Class | Typical paths / content | Backup priority | Notes |
|-------|-------------------------|-----------------|-------|
| A. Essential state | SQLite DBs, profile stores, agent identity | **Critical** | Required for continuity |
| B. Reconstructable cache | `.cache/`, Playwright under image path | Skip or low | Rebuild on demand |
| C. Configuration | `config.yaml`, profile `.env` fragments | **Critical** | Migrate carefully across Hermes versions |
| D. Credentials | Token files, OAuth caches inside data dir | **Critical** (encrypt at rest) | Never put in git |
| E. Sessions | Session DBs / trajectory history | High | User conversation continuity |
| F. Memory | MEMORY.md, USER.md, FTS indexes | High | Learning loop state |
| G. Skills | Custom / generated skills | High | Agent capability growth |
| H. Plugins | Plugin-local state | Medium | Compatibility check on upgrade |
| I. User files | Uploads, exports, workspaces | High | User-created |
| J. Cron / jobs | Cron definitions & run history | High | Scheduled automations |
| K. Profiles / personas | Multi-profile directories | High | SOUL / identity |
| L. Logs | `logs/` | Low | Operational only |

## Rules

1. Production image must never ship user runtime state.
2. Application updates replace `/opt/hermes`; `/opt/data` must survive.
3. Do not blindly restore an old full volume into a newer schema without migration analysis.
4. Prefer selective migration (sessions, memory, skills, profiles, cron) from the old hermes-agent backup.
5. Backup archives from `scripts/backup.sh` must include checksum + git SHA + image digest metadata.
