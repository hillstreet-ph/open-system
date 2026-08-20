#!/usr/bin/env bash
# Apply SQL migrations to a remote Supabase Postgres using DATABASE_URL.
# Requires: psql, DATABASE_URL in env (never commit the value).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
: "${DATABASE_URL:?Set DATABASE_URL to the Supabase Postgres connection string}"
shopt -s nullglob
files=("$ROOT"/supabase/migrations/*.sql)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "no migrations found" >&2
  exit 1
fi
for f in "${files[@]}"; do
  echo "Applying $(basename "$f")..."
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$f"
done
echo "MIGRATIONS_OK"
