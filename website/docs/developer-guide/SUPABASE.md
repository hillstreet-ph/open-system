# Supabase (optional control plane)

Hermes core state remains under `/opt/data` unless you deliberately integrate.

## Use when

- Durable user identities (Auth)
- Shared routing metadata (Telegram agent routes)
- Audit / backup catalog
- pgvector knowledge (if product requires)

## Do not

- Wipe existing project
- Put service-role key in browser
- Put production data in migration files

## Migrations

Versioned SQL only under `supabase/migrations/`. Inspect existing schema before adding tables.

## Automation (see INTEGRATION.md)

- Migrations: `supabase/migrations/`
- Apply: `scripts/supabase/apply-migrations.sh` or workflow `supabase-migrate.yml`
- DB backup: `scripts/supabase/backup-database.sh`
- Deployment record: `scripts/supabase/record-deployment.sh`
- Edge: `supabase/functions/health-ping`, `backup-catalog-ingest`
