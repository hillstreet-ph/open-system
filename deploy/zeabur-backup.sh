#!/usr/bin/env bash
# Online Hermes backup inside the running Zeabur service, onto the persistent
# volume (/opt/data/backups). The backup runs detached in the container so a
# slow archive never hits the Zeabur exec API's request timeout; this script
# then polls for completion.
#
# Usage: deploy/zeabur-backup.sh <label>
# Env:   ZEABUR_CLI (e.g. zeabur@0.24.0), SID, EID; already logged in.
# Output: prints the backup file name on the last line (for off-site copy).
set -euo pipefail

label="${1:-scheduled}"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
name="hermes-backup-${ts}-${label}.zip"
dir=/opt/data/backups
zx() { npx -y "$ZEABUR_CLI" service exec --id "$SID" --env-id "$EID" -i=false -- "$@"; }

zx sh -c "mkdir -p ${dir} && rm -f ${dir}/${name}.done && \
  (nohup sh -c 'HERMES_HOME=/opt/data /opt/hermes/.venv/bin/hermes backup -o ${dir}/${name} -k 7 > ${dir}/${name}.log 2>&1; echo \$? > ${dir}/${name}.done' > /dev/null 2>&1 &) ; echo started"

for i in $(seq 1 60); do # up to ~20 minutes
  sleep 20
  rc="$(zx sh -c "cat ${dir}/${name}.done 2>/dev/null || true" 2>/dev/null | tr -dc 0-9 || true)"
  if [ -n "$rc" ]; then
    zx sh -c "tail -n 5 ${dir}/${name}.log; ls -l ${dir}/${name}" || true
    case "$rc" in
      0) ;;
      1) echo "::warning::hermes backup reported an incomplete archive (kept); see ${dir}/${name}.log" ;;
      *) echo "::error::hermes backup exited ${rc}"; exit 1 ;;
    esac
    echo "$name"
    exit 0
  fi
  echo "waiting for backup (${i})"
done
echo "::error::backup did not finish within 20 minutes"
exit 1
