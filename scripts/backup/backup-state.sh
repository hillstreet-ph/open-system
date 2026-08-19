#!/usr/bin/env bash
# Backup Hermes/Open-System persistent state under HERMES_HOME (/opt/data by default).
# Produces a directory with manifest.json, state archive, and checksums.
# Optional: BACKUP_ENCRYPT_KEY (passphrase) + openssl for local encryption.
# Optional: BACKUP_S3_URI (s3://bucket/prefix) for offsite copy via AWS CLI compatible tools.
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-/opt/data}"
OUT_ROOT="${BACKUP_OUT_DIR:-/tmp/open-system-backups}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
GIT_SHA="${OPEN_SYSTEM_GIT_SHA:-unknown}"
IMAGE_DIGEST="${OPEN_SYSTEM_IMAGE_DIGEST:-unknown}"
DEST="${OUT_ROOT}/backup-${TS}"
mkdir -p "$DEST"

if [[ ! -d "$HERMES_HOME" ]]; then
  echo "error: HERMES_HOME not found: $HERMES_HOME" >&2
  exit 1
fi

# Exclude ephemeral caches and large regeneratable browser downloads
EXCLUDE=(
  --exclude='**/__pycache__'
  --exclude='**/*.pyc'
  --exclude='**/node_modules'
  --exclude='**/.playwright/**'
  --exclude='**/chromium*/**'
  --exclude='**/ffmpeg*/**'
  --exclude='**/logs/**/*.log'
  --exclude='**/.cache/**'
)

tar -C "$(dirname "$HERMES_HOME")" \
  "${EXCLUDE[@]}" \
  -cf "$DEST/state.tar" \
  "$(basename "$HERMES_HOME")"

if command -v zstd >/dev/null 2>&1; then
  zstd -q -f "$DEST/state.tar" -o "$DEST/state.tar.zst"
  rm -f "$DEST/state.tar"
  ARCHIVE="$DEST/state.tar.zst"
else
  gzip -f "$DEST/state.tar"
  ARCHIVE="$DEST/state.tar.gz"
fi

if [[ -n "${BACKUP_ENCRYPT_KEY:-}" ]]; then
  openssl enc -aes-256-cbc -pbkdf2 -salt \
    -in "$ARCHIVE" -out "${ARCHIVE}.enc" \
    -pass env:BACKUP_ENCRYPT_KEY
  rm -f "$ARCHIVE"
  ARCHIVE="${ARCHIVE}.enc"
fi

(
  cd "$DEST"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$(basename "$ARCHIVE")" > checksums.sha256
  else
    shasum -a 256 "$(basename "$ARCHIVE")" > checksums.sha256
  fi
)

python3 - << PY
import json, os, time
dest = os.environ["DEST"]
archive = os.path.basename(os.environ["ARCHIVE"])
manifest = {
  "schema_version": 1,
  "backup_id": os.path.basename(dest),
  "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "hermes_home": os.environ.get("HERMES_HOME", "/opt/data"),
  "git_sha": os.environ.get("GIT_SHA", "unknown"),
  "image_digest": os.environ.get("IMAGE_DIGEST", "unknown"),
  "archive": archive,
  "encrypted": archive.endswith(".enc"),
  "verification_status": "UNVERIFIED",
}
open(os.path.join(dest, "manifest.json"), "w").write(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest, indent=2))
PY

if [[ -n "${BACKUP_S3_URI:-}" ]] && command -v aws >/dev/null 2>&1; then
  aws s3 cp --recursive "$DEST" "${BACKUP_S3_URI%/}/backup-${TS}/"
  echo "uploaded to ${BACKUP_S3_URI%/}/backup-${TS}/"
fi

echo "BACKUP_OK $DEST"
