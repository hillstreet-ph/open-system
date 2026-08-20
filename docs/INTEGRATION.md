# Open-System end-to-end integration

## Architecture

```
GitHub (source + Actions)
    │ docker-release / upstream-sync / backup / migrate
    ▼
Docker Hub (immutable images)
    ▼
Zeabur (runtime + /opt/data volume)
    │
    ├── Hermes state on volume (backup-state.sh)
    └── Supabase (Postgres + optional Auth/Storage/Edge)
            tables, REST API, Edge Functions, cron (pg_cron)
```

## GitHub secrets (names only)

| Secret | Purpose |
|--------|---------|
| `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` | Image publish |
| `SUPABASE_URL` | Project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side REST (never in browser) |
| `DATABASE_URL` | Postgres for migrations & pg_dump |
| `BACKUP_ENCRYPT_KEY` | Optional openssl passphrase |
| `BACKUP_S3_URI` | Optional s3://bucket/prefix |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_DEFAULT_REGION` | Offsite upload |

## Workflows

| Workflow | Schedule / trigger | Action |
|----------|-------------------|--------|
| `backup-scheduled.yml` | Daily 06:00 UTC + manual | Checklist, optional DB dump, sync event |
| `supabase-migrate.yml` | Manual (`confirm=APPLY`) | Apply `supabase/migrations/*.sql` |
| `github-supabase-sync.yml` | After Docker release / manual | Insert `open_system_deployments` |
| `docker-release.yml` | Push main | Publish image |
| `upstream-sync.yml` | Schedule | Upstream PR only |

## Supabase tables

- `open_system_backup_catalog`
- `open_system_deployments`
- `open_system_sync_events`
- `open_system_agents`
- `open_system_telegram_routes`
- `open_system_audit_events`
- `open_system_system_settings`

Apply:

```bash
export DATABASE_URL='postgresql://…'   # from Supabase dashboard
./scripts/supabase/apply-migrations.sh
```

Or: Actions → **Supabase migrations** → `confirm=APPLY`.

## Edge Functions

```bash
supabase functions deploy health-ping
supabase functions deploy backup-catalog-ingest
```

## Volume backup (Zeabur / VPS)

```bash
export HERMES_HOME=/opt/data
export BACKUP_OUT_DIR=/var/backups/open-system
# optional BACKUP_ENCRYPT_KEY BACKUP_S3_URI
./scripts/backup/backup-state.sh
./scripts/backup/verify-backup.sh /var/backups/open-system/backup-…
```

## Cron

1. **GitHub Actions** — `backup-scheduled.yml` daily.
2. **Supabase pg_cron** — optional SQL in migration comments (enable extension in dashboard).
3. **Host cron** — run volume backup on the server that mounts `/opt/data`.

## Safety

- No production wipe
- No secrets in Git
- Migrations are additive / `IF NOT EXISTS`
- Service role key only in GitHub secrets / Zeabur server env
