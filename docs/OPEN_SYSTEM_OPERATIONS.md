# Open-System production operations

This fork (`hillstreet-ph/open-system`) runs Hermes Agent in production from the
**compat image**: the official `nousresearch/hermes-agent:vX.Y.Z` release, pinned by
digest, plus the Open-System MCP tunnel and the `mcp-serve`, `spotify` and `langfuse`
plugins (`deploy/open-system-compat.Dockerfile`).

## Topology

| Item | Value |
|---|---|
| Runtime | Railway project `open-system`, environment `production`, service `hermes-agent` (region asia-southeast1) |
| Start command | `/opt/hermes/docker/entrypoint-dispatch.sh sleep infinity` (keeps `/init` + s6 supervision as PID 1; without it the image runs the interactive CLI, which exits without a TTY and stops the container) |
| Public dashboard / Desktop gateway | `https://open-system.space` (Cloudflare proxied → Railway, container port 9119, login required) |
| OpenAI-compatible API | `https://api.open-system.space/v1` (Cloudflare DNS-only → Railway, container port 8642, `Authorization: Bearer <API_SERVER_KEY>`) |
| Hermes MCP (HTTP) | `https://mcp.open-system.space/mcp` (Cloudflare DNS-only → Railway, container port 8765, `Authorization: Bearer <MCP_HTTP_TOKEN>`; see `deploy/mcp-http/README.md`) |
| Health endpoints | `https://open-system.space/api/status` (gateway + platforms), `https://api.open-system.space/health` |
| Persistent state | Railway volume `hermes-agent-volume` (250 GB, growable) at `/opt/data` (`HERMES_HOME`), owned by uid 10000 (`hermes`) |
| Image registry | Docker Hub `hillstreet/open-system:<version>-compat-<id>` (immutable tags) |
| Deployed release | `deploy/open-system.release` (written by the pipeline) |

The previous Zeabur runtime (`open-system-project` / `hermes-agent-recovery`) is suspended
and kept only as a rollback source; Zeabur shuts down all services on **2026-12-31**.

## Automation

`.github/workflows/open-system-compat-validation.yml` (**Open-System release**)

1. Daily (06:43 Manila) checks Docker Hub for a newer upstream `vX.Y.Z`.
2. Bumps the Dockerfile version + digest, builds, and verifies tunnel, plugins,
   dependency drift and `hermes --version`.
3. Publishes an immutable image tag.
4. Takes a native Railway volume snapshot (`pre-deploy-<tag>`), sets the service image
   via `deploy/railway.sh image`, and waits for `/api/status` to report the new version,
   a running gateway and a connected Telegram platform.
5. On failure it rolls back to the tag in `deploy/open-system.release` and opens an
   `incident` issue. On success it commits the bump + release record to `main`.

Pushes to `main` that touch the Dockerfile, the release file or the workflow run the same
path. Branches named `chore/hermes-v*-compat` only build, validate and publish.

`.github/workflows/open-system-ops.yml` (**Open-System ops**)

- Health every 20 minutes; redeploys the Railway service if unhealthy and keeps a
  single `incident` issue updated (closed automatically on recovery).
- Daily native Railway volume snapshot `daily-YYYYMMDD` (03:17 Manila).

Railway's own volume backup schedule is also enabled (daily, weekly, monthly retention).

Independent monitoring: Sentry uptime monitor **Open System API Health (Railway)**
(`hillstreet` org, project `open-system`) checks `https://api.open-system.space/health`
every minute.

`deploy/railway.sh` accepts either a Railway project token or an account/workspace token
in `RAILWAY_TOKEN` and picks the matching auth header automatically.

## Required settings (names only)

| Name | Kind | Purpose |
|---|---|---|
| `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | secret | publish the image |
| `RAILWAY_TOKEN` | secret | deploy, rollback, redeploy, volume snapshots |
| `RAILWAY_SERVICE_ID` | variable | `hermes-agent` service id |
| `RAILWAY_ENVIRONMENT_ID` | variable | `production` environment id |
| `RAILWAY_VOLUME_INSTANCE_ID` | variable | volume instance of `hermes-agent-volume` |
| `OPEN_SYSTEM_STATUS_URL` | variable, optional | defaults to `https://open-system.space/api/status` |
| `MCP_HTTP_TOKEN` | Railway service variable | bearer token for `mcp.open-system.space`; created by the release workflow, never printed |

Railway service variables (values live only in Railway): `API_SERVER_KEY`,
`HERMES_DASHBOARD*` (incl. basic-auth username/password/hash/secret),
`HERMES_CUSTOM_OPENAI_API_KEY` (open-connect gateway key), `HERMES_BACKUP_TRANSFER_TOKEN`,
`HERMES_BACKUP_ENCRYPTION_KEY`, `HERMES_AUTO_RESTORE=1`, `HERMES_MAX_TOKENS`, `PORT`.
Provider keys used by individual profiles live in each profile's `.env` on the volume.

## Model routing (default profile)

Main: provider `openai` (named provider pointing at `https://open-connect.site/v1`,
key `HERMES_CUSTOM_OPENAI_API_KEY`), model `open-connect/auto`.
Fallbacks: `openai-codex` → `xai-oauth` → `openrouter` (free) → `deepseek`.
Every profile's `.env` carries `HERMES_CUSTOM_OPENAI_API_KEY` so profile gateways, cron
and kanban workers can use the shared provider entry.

## Restore

- Railway snapshot: Railway → `hermes-agent` → Volume → Backups → restore (stop the
  service first; restoring replaces the mounted volume state).
- Empty volume: with `HERMES_AUTO_RESTORE=1`, `scripts/recovery-bootstrap.py` restores the
  newest encrypted off-site backup from Supabase (`open-system-backup-ingest`) on boot.
- New host: run the last image tag from `deploy/open-system.release` with a volume at
  `/opt/data` owned by uid 10000, restore data, recreate the service variables, and use
  the start command above.

## Manual rollback

Railway → `hermes-agent` → Deployments → **Rollback** on the previous successful
deployment, or run the release workflow with `deploy` on an older commit of
`deploy/open-system.release`.

## Connecting Hermes Desktop (macOS)

Settings → Gateways → **Remote gateway**, URL `https://open-system.space`, sign in with
the dashboard credentials, then **Test** (checks both HTTP and WebSocket).
