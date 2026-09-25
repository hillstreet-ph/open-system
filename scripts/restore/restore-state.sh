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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/../backup/verify-backup.sh" "$BACKUP_DIR"
ARCHIVE_NAME="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["archive"])' "$BACKUP_DIR/manifest.json")"
BACKUP_TYPE="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8")).get("type", "state"))' "$BACKUP_DIR/manifest.json")"
if [[ "$BACKUP_TYPE" != "state" ]]; then
  echo "Refusing to restore backup type '$BACKUP_TYPE' as Hermes state" >&2
  exit 4
fi
ARCHIVE="$BACKUP_DIR/$ARCHIVE_NAME"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
SRC="$ARCHIVE"
FORMAT="$ARCHIVE_NAME"
if [[ "$ARCHIVE" == *.enc ]]; then
  [[ -n "${BACKUP_ENCRYPT_KEY:-}" ]] || { echo "BACKUP_ENCRYPT_KEY required for encrypted archive" >&2; exit 1; }
  openssl enc -d -aes-256-cbc -pbkdf2 -in "$ARCHIVE" -out "$TMP/plain" -pass env:BACKUP_ENCRYPT_KEY
  SRC="$TMP/plain"
  FORMAT="${ARCHIVE_NAME%.enc}"
fi
PARENT="$(dirname "$HERMES_HOME")"
mkdir -p "$PARENT"
case "$FORMAT" in
  *.zst) zstd -d -c "$SRC" | tar -C "$PARENT" -xf - ;;
  *.gz)  gzip -dc "$SRC" | tar -C "$PARENT" -xf - ;;
  *.tar) tar -C "$PARENT" -xf "$SRC" ;;
  *) echo "unsupported state archive type: $FORMAT" >&2; exit 1 ;;
esac
echo "RESTORE_OK into $HERMES_HOME"
