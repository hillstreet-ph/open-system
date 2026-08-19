#!/usr/bin/env bash
# Restore a portable Hermes /opt/data archive created by scripts/backup.sh
# Usage: restore.sh <archive.tar.gz> [target_data_dir]

set -euo pipefail

ARCHIVE="${1:-}"
DATA_DIR="${2:-${HERMES_DATA_DIR:-/opt/data}}"
HERMES_UID="${HERMES_UID:-10000}"
HERMES_GID="${HERMES_GID:-10000}"

if [[ -z "$ARCHIVE" || ! -f "$ARCHIVE" ]]; then
  echo "Usage: $0 <hermes-data-XXXX.tar.gz> [/opt/data]" >&2
  exit 1
fi

# Verify checksum if sibling manifest exists
BASE=$(basename "$ARCHIVE")
DIR=$(dirname "$ARCHIVE")
MANIFEST=$(ls "$DIR"/manifest-*.json 2>/dev/null | head -1 || true)
if [[ -n "$MANIFEST" ]]; then
  EXPECTED=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['sha256'])" "$MANIFEST" 2>/dev/null || true)
  if [[ -n "$EXPECTED" ]]; then
    ACTUAL=$(sha256sum "$ARCHIVE" | awk '{print $1}')
    if [[ "$ACTUAL" != "$EXPECTED" ]]; then
      echo "FAIL: checksum mismatch (expected $EXPECTED got $ACTUAL)" >&2
      exit 1
    fi
    echo "OK: checksum verified"
  fi
fi

mkdir -p "$DATA_DIR"
# Extract without overwriting host secrets that may live outside the archive
tar -C "$DATA_DIR" -xzf "$ARCHIVE"

# Fix ownership for non-root runtime
if command -v chown >/dev/null 2>&1; then
  chown -R "${HERMES_UID}:${HERMES_GID}" "$DATA_DIR" 2>/dev/null || true
fi

echo "OK: restored $ARCHIVE -> $DATA_DIR"
echo "Next: provide env secrets, start container, run scripts/healthcheck.sh"
