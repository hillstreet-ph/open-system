#!/usr/bin/env bash
# Verify a state or PostgreSQL backup directory.
set -euo pipefail
BACKUP_DIR="${1:-}"
if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
  echo "usage: $0 /path/to/backup-DIR" >&2
  exit 2
fi
cd "$BACKUP_DIR"
[[ -f manifest.json ]] || { echo "missing manifest.json" >&2; exit 1; }
[[ -f checksums.sha256 ]] || { echo "missing checksums.sha256" >&2; exit 1; }
if command -v sha256sum >/dev/null 2>&1; then
  sha256sum -c checksums.sha256
else
  shasum -a 256 -c checksums.sha256
fi
ARCHIVE="$(python3 -c 'import json; print(json.load(open("manifest.json", encoding="utf-8"))["archive"])')"
[[ -f "$ARCHIVE" ]] || { echo "missing archive $ARCHIVE" >&2; exit 1; }
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SRC="$ARCHIVE"
FORMAT="$ARCHIVE"
if [[ "$ARCHIVE" == *.enc ]]; then
  [[ -n "${BACKUP_ENCRYPT_KEY:-}" ]] || { echo "BACKUP_ENCRYPT_KEY required for encrypted archive" >&2; exit 1; }
  openssl enc -d -aes-256-cbc -pbkdf2 -in "$ARCHIVE" -out "$TMP/plain" -pass env:BACKUP_ENCRYPT_KEY
  SRC="$TMP/plain"
  FORMAT="${ARCHIVE%.enc}"
fi
case "$FORMAT" in
  *.zst) zstd -d -c "$SRC" | tar -t >/dev/null ;;
  *.gz)  gzip -dc "$SRC" | tar -t >/dev/null ;;
  *.tar) tar -tf "$SRC" >/dev/null ;;
  *.dump)
    command -v pg_restore >/dev/null 2>&1 || { echo "pg_restore required for PostgreSQL custom dumps" >&2; exit 1; }
    pg_restore --list "$SRC" >/dev/null
    ;;
  *) echo "unknown archive type: $FORMAT" >&2; exit 1 ;;
esac
python3 - <<'PY'
import json

with open("manifest.json", encoding="utf-8") as manifest_file:
    manifest = json.load(manifest_file)
manifest["verification_status"] = "VERIFIED"
with open("manifest.json", "w", encoding="utf-8") as manifest_file:
    manifest_file.write(json.dumps(manifest, indent=2) + "\n")
print("VERIFIED", manifest.get("backup_id"))
PY
