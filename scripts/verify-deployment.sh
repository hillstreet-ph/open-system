#!/usr/bin/env bash
# Post-deploy verification for Open-System on any Docker host / Zeabur

set -euo pipefail

echo "=== Open-System deployment verification ==="

./scripts/healthcheck.sh

echo ""
echo "=== Suggested manual checks ==="
echo "1. Dashboard UI loads (port ${HERMES_DASHBOARD_PORT:-9119})"
echo "2. API /v1/models returns 200 with Bearer token (port ${API_SERVER_PORT:-8642})"
echo "3. Sessions / memory / skills present under ${HERMES_DATA_DIR:-/opt/data}"
echo "4. Cron definitions intact if previously configured"
echo "5. Record image digest + git SHA for rollback"
echo ""
echo "Rollback: redeploy previous image digest; restore /opt/data backup if needed."
