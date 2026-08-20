#!/usr/bin/env bash
# Logical backup of Supabase Postgres (schema+data). Encrypt optional.
set -euo pipefail
: "${DATABASE_URL:?Set DATABASE_URL}"
OUT_ROOT="${BACKUP_OUT_DIR:-/tmp/open-system-backups}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${OUT_ROOT}/db-${TS}"
mkdir -p "$DEST"
DUMP="$DEST/database.dump"
if command -v pg_dump >/dev/null 2>&1; then
  pg_dump --format=custom --no-owner --no-acl -f "$DUMP" "$DATABASE_URL"
else
  echo "pg_dump not found; install PostgreSQL client tools" >&2
  exit 1
fi
if [[ -n "${BACKUP_ENCRYPT_KEY:-}" ]]; then
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$DUMP" -out "${DUMP}.enc" -pass env:BACKUP_ENCRYPT_KEY
  rm -f "$DUMP"
  DUMP="${DUMP}.enc"
fi
(
  cd "$DEST"
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$(basename "$DUMP")" > checksums.sha256
  else shasum -a 256 "$(basename "$DUMP")" > checksums.sha256
  fi
)
python3 - << PY
import json, os, time
dest=os.environ["DEST"]
dump=os.path.basename(os.environ["DUMP"])
m={
  "schema_version":1,
  "backup_id":os.path.basename(dest),
  "created_at":time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "type":"postgres",
  "archive":dump,
  "encrypted":dump.endswith(".enc"),
  "verification_status":"UNVERIFIED",
  "git_sha":os.environ.get("OPEN_SYSTEM_GIT_SHA","unknown"),
}
open(os.path.join(dest,"manifest.json"),"w").write(json.dumps(m,indent=2)+"\n")
print(json.dumps(m,indent=2))
PY
if [[ -n "${BACKUP_S3_URI:-}" ]] && command -v aws >/dev/null 2>&1; then
  aws s3 cp --recursive "$DEST" "${BACKUP_S3_URI%/}/db-${TS}/"
fi
echo "DB_BACKUP_OK $DEST"
