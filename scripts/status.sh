#!/usr/bin/env bash
# Operational status (secrets redacted).
set -euo pipefail
HERMES_HOME="${HERMES_HOME:-/opt/data}"
echo "=== Open-System status ==="
echo "time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "hostname: $(hostname 2>/dev/null || echo unknown)"
echo "HERMES_HOME: $HERMES_HOME"
if [[ -d "$HERMES_HOME" ]]; then
  echo "volume: present"
  du -sh "$HERMES_HOME" 2>/dev/null || true
else
  echo "volume: MISSING"
fi
echo "OPEN_SYSTEM_GIT_SHA: ${OPEN_SYSTEM_GIT_SHA:-unset}"
echo "OPEN_SYSTEM_IMAGE_DIGEST: ${OPEN_SYSTEM_IMAGE_DIGEST:-unset}"
echo "API_SERVER_ENABLED: ${API_SERVER_ENABLED:-unset}"
echo "HERMES_DASHBOARD: ${HERMES_DASHBOARD:-unset}"
echo "TELEGRAM_BOT_TOKEN: $([[ -n "${TELEGRAM_BOT_TOKEN:-}" ]] && echo set || echo unset)"
echo "SUPABASE_URL: ${SUPABASE_URL:-unset}"
echo "OPENROUTER_API_KEY: $([[ -n "${OPENROUTER_API_KEY:-}" ]] && echo set || echo unset)"
# Local probes (no secrets printed)
API_PORT="${API_SERVER_PORT:-8642}"
DASH_PORT="${HERMES_DASHBOARD_PORT:-9119}"
if command -v curl >/dev/null 2>&1; then
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${API_PORT}/health" 2>/dev/null || echo 000)
  echo "api_health_http: $code"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "http://127.0.0.1:${DASH_PORT}/" 2>/dev/null || echo 000)
  echo "dashboard_http: $code"
fi
echo "=== end ==="
