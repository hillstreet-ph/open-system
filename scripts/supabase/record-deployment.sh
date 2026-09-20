#!/usr/bin/env bash
# Record a deployment row into Supabase (REST). Uses service role server-side only.
set -euo pipefail
: "${SUPABASE_URL:?}"
: "${SUPABASE_SERVICE_ROLE_KEY:?}"
GIT_SHA="${OPEN_SYSTEM_GIT_SHA:-unknown}"
IMAGE_REF="${OPEN_SYSTEM_IMAGE_REF:-unknown}"
IMAGE_DIGEST="${OPEN_SYSTEM_IMAGE_DIGEST:-unknown}"
ENV_NAME="${OPEN_SYSTEM_ENV:-production}"
BODY=$(GIT_SHA="$GIT_SHA" IMAGE_REF="$IMAGE_REF" IMAGE_DIGEST="$IMAGE_DIGEST" \
  ENV_NAME="$ENV_NAME" python3 -c "import json,os; print(json.dumps({
  'git_sha': os.environ.get('GIT_SHA','unknown'),
  'image_ref': os.environ.get('IMAGE_REF','unknown'),
  'image_digest': os.environ.get('IMAGE_DIGEST','unknown'),
  'environment': os.environ.get('ENV_NAME','production'),
  'status': 'recorded',
}))")
# Never print a provider response body: errors may contain sensitive metadata.
# Do not follow redirects with the service-role headers.
if ! HTTP_STATUS=$(curl --silent --output /dev/null --write-out '%{http_code}' \
  --connect-timeout 10 --max-time 30 \
  -X POST "${SUPABASE_URL%/}/rest/v1/open_system_deployments" \
  -H "apikey: ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Authorization: Bearer ${SUPABASE_SERVICE_ROLE_KEY}" \
  -H "Content-Type: application/json" \
  -H "Prefer: return=minimal" \
  -d "$BODY"); then
  echo "Artifact record request failed before HTTP confirmation." >&2
  exit 1
fi
# A row is confirmed only after Supabase returns a 2xx response.
case "$HTTP_STATUS" in
  2[0-9][0-9]) echo "DEPLOYMENT_RECORDED" ;;
  *)
    echo "Artifact record rejected (HTTP ${HTTP_STATUS})." >&2
    exit 1
    ;;
esac
