#!/usr/bin/env bash
# Open-System / Hermes health verification
# Safe for use as Docker HEALTHCHECK or external probe.
# Does not require privileged credentials.

set -euo pipefail

API_PORT="${API_SERVER_PORT:-8642}"
DASH_PORT="${HERMES_DASHBOARD_PORT:-9119}"
DATA_DIR="${HERMES_DATA_DIR:-/opt/data}"
TIMEOUT="${HEALTHCHECK_TIMEOUT:-5}"

fail() { echo "FAIL: $*" >&2; exit 1; }
ok()   { echo "OK: $*"; }

# 1. Persistent volume writable
if [[ ! -d "$DATA_DIR" ]]; then
  fail "$DATA_DIR does not exist"
fi
if ! touch "$DATA_DIR/.healthcheck_write" 2>/dev/null; then
  fail "$DATA_DIR is not writable"
fi
rm -f "$DATA_DIR/.healthcheck_write"
ok "$DATA_DIR writable"

# 2. Core processes (s6-supervised when present)
if command -v pgrep >/dev/null 2>&1; then
  if pgrep -f 's6-svscan|hermes|gateway' >/dev/null 2>&1; then
    ok "Hermes-related process(es) running"
  else
    # Soft warn: some minimal CMD overrides may still be healthy
    echo "WARN: no hermes/gateway/s6 process matched" >&2
  fi
fi

# 3. Dashboard (optional — only if enabled)
if [[ "${HERMES_DASHBOARD:-}" =~ ^(1|true|yes|TRUE|YES)$ ]]; then
  if curl -fsS -m "$TIMEOUT" -o /dev/null "http://127.0.0.1:${DASH_PORT}/" 2>/dev/null \
     || curl -fsS -m "$TIMEOUT" -o /dev/null "http://127.0.0.1:${DASH_PORT}/health" 2>/dev/null; then
    ok "Dashboard reachable on :${DASH_PORT}"
  else
    fail "Dashboard not reachable on :${DASH_PORT}"
  fi
fi

# 4. API server (optional — only if enabled)
if [[ "${API_SERVER_ENABLED:-}" =~ ^(1|true|yes|TRUE|YES)$ ]]; then
  # Prefer unauthenticated health if available; fall back to models with key
  if curl -fsS -m "$TIMEOUT" -o /dev/null "http://127.0.0.1:${API_PORT}/health" 2>/dev/null; then
    ok "API health on :${API_PORT}"
  elif [[ -n "${API_SERVER_KEY:-}" ]]; then
    code=$(curl -sS -m "$TIMEOUT" -o /dev/null -w "%{http_code}" \
      -H "Authorization: Bearer ${API_SERVER_KEY}" \
      "http://127.0.0.1:${API_PORT}/v1/models" || echo "000")
    if [[ "$code" == "200" ]]; then
      ok "API /v1/models on :${API_PORT}"
    else
      fail "API not healthy on :${API_PORT} (HTTP $code)"
    fi
  else
    fail "API_SERVER_ENABLED but no /health and no API_SERVER_KEY for probe"
  fi
fi

ok "healthcheck passed"
exit 0
