#!/usr/bin/env bash
# Record a deployment row into Supabase (REST). Uses service role server-side only.
set -euo pipefail
: "${SUPABASE_URL:?}"
: "${SUPABASE_SERVICE_ROLE_KEY:?}"
GIT_SHA="${OPEN_SYSTEM_GIT_SHA:-unknown}"
IMAGE_REF="${OPEN_SYSTEM_IMAGE_REF:-unknown}"
IMAGE_DIGEST="${OPEN_SYSTEM_IMAGE_DIGEST:-unknown}"
ENV_NAME="${OPEN_SYSTEM_ENV:-production}"
BODY=$(python3 -c "import json,os; print(json.dumps({
  'git_sha': os.environ.get('GIT_SHA','unknown'),
  'image_ref': os.environ.get('IMAGE_REF','unknown'),
  'image_digest': os.environ.get('IMAGE_DIGEST','unknown'),
  'environment': os.environ.get('ENV_NAME','production'),
  'status': 'recorded',
}))")
curl -sS -X POST "${SUPABASE_URL%/}/rest/v1/open_system_deployments" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d "$BODY"
echo
echo "DEPLOYMENT_RECORDED"
