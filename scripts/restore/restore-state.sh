#!/usr/bin/env bash
# Restore Hermes state from a verified backup directory into HERMES_HOME.
# DANGEROUS: overwrites files under HERMES_HOME. Prefer empty volume for DR drills.
set -euo pipefail
BACKUP_DIR="${1:-}"
HERMES_HOME="${HERMES_HOME:-/opt/data}"
if [[ -z "$BACKUP_DIR" || ! -d "$BACKUP_DIR" ]]; then
  echo "usage: $0 /path/to/backup-DIR" >&2
  exit 2
fi
if [[ "${RESTORE_CONFIRM:-}" != "YES" ]]; then
  echo "Refusing: set RESTORE_CONFIRM=YES to restore into $HERMES_HOME" >&2
  exit 3
fi
"$BACKUP_DIR/../backup/verify-backup.sh" "$BACKUP_DIR" 2>/dev/null || scripts/backup/verify-backup.sh "$BACKUP_DIR"
ARCHIVE_NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["archive"])' "$BACKUP_DIR/manifest.json")"
ARCHIVE="$BACKUP_DIR/$ARCHIVE_NAME"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SRC="$ARCHIVE"
if [[ "$ARCHIVE" == *.enc ]]; then
  openssl enc -d -aes-256-cbc -pbkdf2 -in "$ARCHIVE" -out "$TMP/plain" -pass env:BACKUP_ENCRYPT_KEY
  SRC="$TMP/plain"
fi
PARENT="$(dirname "$HERMES_HOME")"
mkdir -p "$PARENT"
case "$SRC" in
  *.zst) zstd -d -c "$SRC" | tar -C "$PARENT" -xf - ;;
  *.gz)  gzip -dc "$SRC" | tar -C "$PARENT" -xf - ;;
  *.tar) tar -C "$PARENT" -xf "$SRC" ;;
esac
echo "RESTORE_OK into $HERMES_HOME"
