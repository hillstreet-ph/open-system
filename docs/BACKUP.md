# Backup

## Local / volume backup

```bash
export HERMES_HOME=/opt/data
export BACKUP_OUT_DIR=/var/backups/open-system
# optional:
# export BACKUP_ENCRYPT_KEY='…'   # openssl AES
# export BACKUP_S3_URI='s3://bucket/open-system'
# export OPEN_SYSTEM_GIT_SHA=…
# export OPEN_SYSTEM_IMAGE_DIGEST=sha256:…

./scripts/backup/backup-state.sh
./scripts/backup/verify-backup.sh /var/backups/open-system/backup-TIMESTAMP
```

## Triggers

| Trigger | How |
|---------|-----|
| Scheduled | GitHub Actions `backup-scheduled.yml` (optional) or external cron |
| Manual | Run script on host / one-off Action |
| Pre-deploy | Operator checklist before production image pin change |
| Pre-migration | Required before Supabase or config schema migrations |

## Rules

- Do **not** store backups in Git
- Do **not** rely only on GitHub Actions artifacts for long-term retention
- Prefer S3-compatible offsite storage + encryption
- A backup is **UNVERIFIED** until `verify-backup.sh` succeeds

## Supabase

Use Supabase dashboard / `pg_dump` with project credentials stored only in secret managers.
Schema changes must live under `supabase/migrations/` (no production data in migrations).
