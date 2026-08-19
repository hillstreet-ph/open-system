#!/usr/bin/env bash
# Portable /opt/data backup for Open-System / Hermes
# Produces a versioned archive + manifest. Does NOT include plaintext secrets
# from the environment — only filesystem state under the data dir.

set -euo pipefail

DATA_DIR="${HERMES_DATA_DIR:-/opt/data}"
OUT_DIR="${BACKUP_OUT_DIR:-./backups}"
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
GIT_SHA="${HERMES_GIT_SHA:-unknown}"
IMAGE_DIGEST="${OPEN_SYSTEM_IMAGE_DIGEST:-unknown}"
ARCHIVE_NAME="hermes-data-${STAMP}.tar.gz"
MANIFEST_NAME="manifest-${STAMP}.json"

mkdir -p "$OUT_DIR"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

echo "Backing up $DATA_DIR -> $OUT_DIR/$ARCHIVE_NAME"

# Exclude volatile caches if present (reconstructable)
tar -C "$DATA_DIR" \
  --exclude='./.cache' \
  --exclude='./tmp' \
  --exclude='./.playwright' \
  --exclude='./logs/*.log' \
  -czf "$TMP/$ARCHIVE_NAME" .

cp "$TMP/$ARCHIVE_NAME" "$OUT_DIR/$ARCHIVE_NAME"
CHECKSUM=$(sha256sum "$OUT_DIR/$ARCHIVE_NAME" | awk '{print $1}')

cat > "$OUT_DIR/$MANIFEST_NAME" <<EOF
{
  "format": "open-system-hermes-backup-v1",
  "created_at": "$STAMP",
  "git_sha": "$GIT_SHA",
  "image_digest": "$IMAGE_DIGEST",
  "data_dir": "$DATA_DIR",
  "archive": "$ARCHIVE_NAME",
  "sha256": "$CHECKSUM",
  "hostname": "$(hostname 2>/dev/null || echo unknown)",
  "notes": "Restore with scripts/restore.sh. Do not embed env secrets in this archive."
}
EOF

echo "OK: archive=$OUT_DIR/$ARCHIVE_NAME"
echo "OK: sha256=$CHECKSUM"
echo "OK: manifest=$OUT_DIR/$MANIFEST_NAME"
