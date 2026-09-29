#!/usr/bin/env bash
set -euo pipefail

repo="${1:-.}"
[[ -d "$repo" ]] || { echo "Repository path not found: $repo" >&2; exit 2; }
cd "$repo"
echo "platform-audit-root=$(pwd)"
echo "git-branch=$(git branch --show-current 2>/dev/null || echo unavailable)"
patterns='railway|RAILWAY_|railway\.app|zeabur|ZEABUR_|cloudflare|CLOUDFLARE_|supabase|SUPABASE_|sentry|SENTRY_|dockerhub|DOCKERHUB_'
command -v rg >/dev/null 2>&1 || { echo "rg is required" >&2; exit 3; }
rg -n -i --hidden --glob '!.git/**' --glob '!node_modules/**' --glob '!vendor/**' --glob '!dist/**' --glob '!build/**' "$patterns" . \
  | sed -E 's/((token|secret|password|key)[[:space:]]*[:=][[:space:]]*)[^[:space:]]+/\1[REDACTED]/Ig' || true
echo "workflow-files"
find .github/workflows -maxdepth 1 -type f -print 2>/dev/null | sort || true
echo "container-files"
find . -maxdepth 3 -type f \( -iname 'Dockerfile*' -o -iname 'compose*.yml' -o -iname 'compose*.yaml' \) -print | sort
