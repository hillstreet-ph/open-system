# Disaster recovery

## Goal

Recover Open-System on a **new** Linux host without rebuilding from scratch.

## Inputs

1. GitHub repo `hillstreet-ph/open-system` (known commit)
2. Docker image **digest** (e.g. `kairocasino/open-system@sha256:…`)
3. Secrets (Zeabur/GitHub/1Password — never from Git)
4. Verified backup directory (state + checksums)
5. Supabase project (or restored database)

## Procedure

1. Provision host with Docker
2. Create volume path `/opt/data`
3. Restore: `RESTORE_CONFIRM=YES HERMES_HOME=/opt/data ./scripts/restore/restore-state.sh /path/to/backup-…`
4. Pull image by digest
5. Run container with same env **names** as production (values from secret store)
6. Mount `/opt/data`
7. Publish ports: API 8642, dashboard 9119 (dashboard requires basic-auth env)
8. `./scripts/healthcheck.sh` / `./scripts/status.sh`
9. Verify Telegram allowlist user can message the bot
10. Verify Supabase connectivity if used
11. Switch DNS/traffic

## Rollback (application)

Pin previous **digest** only. Do **not** restore an old DB backup for ordinary app rollback unless a migration requires it.

## Non-negotiables

- No database reset
- No volume wipe for ordinary recovery drills on production
- No secrets in Git
