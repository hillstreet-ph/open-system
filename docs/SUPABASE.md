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
