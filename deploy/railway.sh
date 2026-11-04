#!/usr/bin/env bash
# Railway control helper for the open-system production service (GraphQL public API).
#
# Env: RAILWAY_TOKEN (project token or account/workspace token; auto-detected), RAILWAY_SERVICE_ID,
#      RAILWAY_ENVIRONMENT_ID, optional RAILWAY_VOLUME_INSTANCE_ID (for backups).
#
#   railway.sh image <docker-image-ref>   set the service image and deploy it
#   railway.sh redeploy                   redeploy the current image (self-heal)
#   railway.sh backup <name>              snapshot the persistent volume (native Railway backup)
#   railway.sh current-image              print the image currently configured
#   railway.sh ensure-secret <NAME>       create a random service variable if absent (value never printed;
#                                         applied on the next deploy)
set -euo pipefail

API="https://backboard.railway.com/graphql/v2"
: "${RAILWAY_TOKEN:?}" "${RAILWAY_SERVICE_ID:?}" "${RAILWAY_ENVIRONMENT_ID:?}"

# RAILWAY_TOKEN may be a project token (Project-Access-Token header) or an account/workspace
# token (Authorization: Bearer). Detect once: only a project token can read `projectToken`.
auth_header() {
  if [ -z "${RAILWAY_AUTH_HEADER:-}" ]; then
    if curl -fsS --max-time 30 "$API" -H "Project-Access-Token: $RAILWAY_TOKEN" -H 'Content-Type: application/json' \
         -d '{"query":"{ projectToken { projectId } }"}' 2>/dev/null | grep -q '"projectId"'; then
      RAILWAY_AUTH_HEADER="Project-Access-Token: $RAILWAY_TOKEN"
    else
      RAILWAY_AUTH_HEADER="Authorization: Bearer $RAILWAY_TOKEN"
    fi
  fi
  printf '%s' "$RAILWAY_AUTH_HEADER"
}

gql() {
  local payload hdr
  payload="$(python3 -c 'import json,sys; print(json.dumps({"query": sys.argv[1], "variables": json.loads(sys.argv[2])}))' "$1" "$2")"
  hdr="$(auth_header)"
  local out
  out="$(curl -fsS --retry 3 --max-time 60 "$API" -H "$hdr" \
        -H 'Content-Type: application/json' -d "$payload")"
  if printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(1 if d.get("errors") else 0)'; then
    printf '%s' "$out"
  else
    echo "Railway API error: $(printf '%s' "$out" | head -c 400)" >&2
    return 1
  fi
}

vars() {
  python3 -c 'import json,os,sys; d={"s":os.environ["RAILWAY_SERVICE_ID"],"e":os.environ["RAILWAY_ENVIRONMENT_ID"]}; d.update(dict(a.split("=",1) for a in sys.argv[1:])); print(json.dumps(d))' "$@"
}

case "${1:-}" in
  image)
    img="${2:?image ref}"
    gql 'mutation($s:String!,$e:String!,$i:String!){serviceInstanceUpdate(serviceId:$s,environmentId:$e,input:{source:{image:$i}})}' "$(vars "i=$img")" >/dev/null
    gql 'mutation($s:String!,$e:String!){serviceInstanceDeployV2(serviceId:$s,environmentId:$e)}' "$(vars)" >/dev/null
    echo "deployed $img"
    ;;
  redeploy)
    gql 'mutation($s:String!,$e:String!){serviceInstanceRedeploy(serviceId:$s,environmentId:$e)}' "$(vars)" >/dev/null
    echo "redeploy requested"
    ;;
  backup)
    : "${RAILWAY_VOLUME_INSTANCE_ID:?}"
    gql 'mutation($v:String!,$n:String){volumeInstanceBackupCreate(volumeInstanceId:$v,name:$n){workflowId}}' \
      "$(python3 -c 'import json,os,sys; print(json.dumps({"v":os.environ["RAILWAY_VOLUME_INSTANCE_ID"],"n":sys.argv[1]}))' "${2:-manual}")" >/dev/null
    echo "volume backup requested: ${2:-manual}"
    ;;
  current-image)
    gql 'query($s:String!,$e:String!){serviceInstance(serviceId:$s,environmentId:$e){source{image}}}' "$(vars)" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["serviceInstance"]["source"]["image"] or "")'
    ;;
  ensure-secret)
    name="${2:?variable name}"
    case "$name" in *[!A-Z0-9_]*) echo "invalid variable name" >&2; exit 2 ;; esac
    project="$(gql 'query($s:String!){service(id:$s){projectId}}' "$(vars)" \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["service"]["projectId"])')"
    if gql 'query($p:String!,$s:String!,$e:String!){variables(projectId:$p,serviceId:$s,environmentId:$e)}' "$(vars "p=$project")" \
         | NAME="$name" python3 -c 'import json,os,sys; sys.exit(0 if os.environ["NAME"] in json.load(sys.stdin)["data"]["variables"] else 1)'; then
      echo "$name already set; left unchanged"
    else
      payload="$(NAME="$name" P="$project" python3 -c '
import json, os, secrets
print(json.dumps({"p": os.environ["P"], "s": os.environ["RAILWAY_SERVICE_ID"], "e": os.environ["RAILWAY_ENVIRONMENT_ID"],
                  "n": os.environ["NAME"], "v": secrets.token_urlsafe(48)}))')"
      gql 'mutation($p:String!,$s:String!,$e:String!,$n:String!,$v:String!){variableUpsert(input:{projectId:$p,serviceId:$s,environmentId:$e,name:$n,value:$v,skipDeploys:true})}' "$payload" >/dev/null
      unset payload
      echo "$name created (value stored only in Railway)"
    fi
    ;;
  *)
    echo "usage: $0 image <ref> | redeploy | backup <name> | current-image | ensure-secret <NAME>" >&2; exit 2 ;;
esac
