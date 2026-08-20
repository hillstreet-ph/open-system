#!/usr/bin/env bash
# Install curated official optional skills into the active Hermes profile.
# Run inside the Open-System container or any host with `hermes` CLI:
#   export HERMES_HOME=/opt/data
#   ./scripts/enablement/install-official-skills.sh
set -euo pipefail

HERMES_HOME="${HERMES_HOME:-${HOME}/.hermes}"
export HERMES_HOME

if ! command -v hermes >/dev/null 2>&1; then
  echo "hermes CLI not found on PATH. Run this inside the open-system container." >&2
  exit 1
fi

# Curated for system development & operations (not every catalog entry).
SKILLS=(
  official/devops/docker-management
  official/devops/hermes-s6-container-supervision
  official/devops/watchers
  official/research/duckduckgo-search
  official/research/searxng-search
  official/research/osint-investigation
  official/software-development
  official/mcp/fastmcp
  official/mcp/mcporter
  official/web-development/page-agent
  official/productivity
)

echo "HERMES_HOME=$HERMES_HOME"
for s in "${SKILLS[@]}"; do
  echo "=== install $s ==="
  hermes skills install "$s" || echo "WARN: failed $s (may already exist or path differs)"
done

echo "=== enable plugins (config merge may still be required) ==="
for p in disk-cleanup security-guidance memory web/ddgs cron_providers/chronos; do
  hermes plugins enable "$p" 2>/dev/null || echo "WARN: enable $p"
done

echo "=== skills list (sample) ==="
hermes skills list 2>/dev/null | head -40 || true
echo "DONE — restart gateway/dashboard session if skills do not appear yet"
