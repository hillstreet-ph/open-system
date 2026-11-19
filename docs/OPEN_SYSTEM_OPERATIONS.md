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

Off-site: the image runs the s6 service `hermes-offsite-backup` (`deploy/offsite-backup/`). Every
`OFFSITE_BACKUP_INTERVAL_HOURS` (default 6, first run 15 minutes after boot) it creates a
consistent `hermes backup`, encrypts it in Fernet parts with `HERMES_BACKUP_ENCRYPTION_KEY` and
uploads it to Supabase through `open-system-backup-ingest` (`HERMES_BACKUP_TRANSFER_TOKEN`). The
server verifies each part and the manifest; the newest verified backup is what auto-restore uses.
Last success: `/opt/data/backups/offsite/last-success`; logs: `[offsite-backup]` lines.

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
`HERMES_DASHBOARD*` (incl. basic-auth username/password/hash/secret and
`HERMES_DASHBOARD_SESSION_TOKEN`, the Desktop remote-gateway token),
`HERMES_CUSTOM_OPENAI_API_KEY` (open-connect gateway key), `HERMES_BACKUP_TRANSFER_TOKEN`,
`HERMES_BACKUP_ENCRYPTION_KEY`, `HERMES_AUTO_RESTORE=1`, `HERMES_MAX_TOKENS`, `PORT`.
Provider keys used by individual profiles live in each profile's `.env` on the volume.

## Model routing (default profile)

Main: provider `openai` (named provider pointing at `https://open-connect.site/v1`,
key `HERMES_CUSTOM_OPENAI_API_KEY`), model `open-connect/auto`.
Fallbacks: `openai-codex` → `xai-oauth` → `openrouter` (free) → `deepseek`.
Every profile's `.env` carries `HERMES_CUSTOM_OPENAI_API_KEY` so profile gateways, cron
and kanban workers can use the shared provider entry.

## Execution sandbox

Agent terminal, file and `execute_code` calls do not run inside the Hermes container. Every profile
uses `terminal.backend: ssh` to the separate Railway service `open-system-sandbox` (image
`hillstreet/open-system-sandbox`, built from `deploy/sandbox` by `.github/workflows/open-system-sandbox.yml`):

- reached only over Railway private networking: `open-system-sandbox.railway.internal:2222`, no public domain;
- key-only SSH as the unprivileged user `agent`, no root login, no forwarding;
- persistent workspace `/data/home/workspace` on the sandbox volume; Python 3.12, Node 22, git, build tools;
- no access to `/opt/data` or the Hermes secrets; only variables a skill declares (or
  `terminal.env_passthrough` lists) are forwarded, never provider credentials.

| Variable | Service | Purpose |
|---|---|---|
| `SANDBOX_HOST_KEY` | open-system-sandbox | sandbox SSH host key (fixed, so redeploys keep the identity) |
| `SANDBOX_AUTHORIZED_KEYS` | open-system-sandbox | Hermes public key |
| `SANDBOX_SSH_PRIVATE_KEY` | hermes-agent | Hermes key; `cont-init 017-sandbox-ssh` writes it to `/opt/data/.ssh/sandbox_ed25519` |
| `SANDBOX_SSH_KNOWN_HOSTS` | hermes-agent | pinned sandbox host key (`/opt/data/.ssh/known_hosts2`) |
| `SANDBOX_RAILWAY_SERVICE_ID` | GitHub variable | lets the sandbox workflow deploy new images |

Admin actions: `sandbox` points every profile at the sandbox (the scheduled `guard` re-applies it if a
profile drifts back to `local`); `sandbox-check` asks the agent through the API server to run
`whoami` and checks it ran as `agent` without seeing `/opt/data`. To fall back to the container, remove
`SANDBOX_SSH_PRIVATE_KEY` from hermes-agent and set `terminal.backend: local` in the profiles.
Host-level work (Hermes CLI, `/opt/data`) belongs to the admin/ops workflows, not to agent chats.
`procs` now reports the sandbox's processes, not the Hermes container's.

## Broken config.yaml

When a `config.yaml` stops parsing, Hermes runs on built-in defaults (no open-connect routing, no
MCP servers, `/api/status` shows `gateway_state: startup_failed`) and refuses every API write over
the file. On each container start, `/etc/cont-init.d/016-config-repair`
(`deploy/config-repair/config_repair.py`) checks the default and every profile `config.yaml`; a
file that does not parse is copied to `<home>/backups/config/config.yaml.unparseable-<UTC>` and
only the lines the parser rejects are removed (key names are logged, values never). To apply it,
restart the service (Railway → `hermes-agent` → Restart). The release health gate and the ops
probe both fail on `startup_failed`.

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

Settings → Gateways (Cmd+, → Gateways, or the plug icon at the end of the profile rail) →
**Add connection** → **Remote gateway**:

- Name: `Railway` (any unique name)
- Gateway URL: `https://open-system.space`
- Authentication: **Session token** — the value of the Railway variable
  `HERMES_DASHBOARD_SESSION_TOKEN` (Railway → `hermes-agent` → Variables; it is a password:
  rotating it means pasting the new value into Desktop). Browser sign-in at
  https://open-system.space keeps using the dashboard username/password.

Click **Test** (it checks both HTTP and WebSocket), then **Make primary** so new sessions,
profiles and cron jobs land on the cloud gateway. The Mac's local runtime stays listed as
**Local**; both stay connected.

### Moving local Mac data into the cloud

1. On the Mac, export each local profile you want in the cloud:
   `hermes profile export <name>` (writes `<name>.tar.gz`; API keys are stripped).
2. Copy it to the container (`scp <name>.tar.gz open-system:/opt/data/` after the SSH setup
   below) and install it there as the hermes user: `hermes profile import /opt/data/<name>.tar.gz`.
   Desktop also offers **⌘K → Export/Import profile…**.
3. Keys are not exported: the cloud profiles read the shared provider key from their `.env`.
   Never copy the Mac's `config.yaml`/`.env` over the cloud ones wholesale.

### SSH into the Railway container

`railway ssh` needs the Railway CLI logged in as a workspace member (`railway login`) and an SSH
key registered with Railway (the CLI offers to register `~/.ssh/id_ed25519.pub` the first time).
Project tokens cannot register keys.

```bash
railway link --project d42d3394-bffe-442b-ba37-e1d2bf55edce --service hermes-agent
railway ssh                       # shell in the container (user root; Hermes runs as hermes)
railway ssh config --service hermes-agent --alias open-system   # then: ssh open-system
```

Inside: `su hermes -s /bin/bash`, `HERMES_HOME=/opt/data hermes gateway migrate --multiplex --dry-run`.
