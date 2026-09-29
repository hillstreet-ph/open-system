# Provider validation matrix

## GitHub

- Default branch, protection/rulesets, CODEOWNERS, required checks, environments, OIDC, Dependabot, secret scanning, release workflow.
- Auto-merge only for approved dependency or agent PRs after all checks and review policy pass.

## Docker Hub

- Ownership, scoped token, immutable tags, multi-stage/non-root image, SBOM, vulnerability scan, provenance, retention.

## Cloudflare

- Account/zone ownership, DNS, TLS mode, WAF/rate limiting, Pages/Workers bindings, routes, caches, logs, R2 backup policy where used.

## Supabase

- Environment mapping, migrations, RLS, Auth redirect allowlist, OAuth, Storage policies, Vault/Edge secrets, Realtime, vector extension/index, scheduled jobs, backups, restore test.
- Use service-role keys only on trusted servers.

## Sentry

- Organization/project mapping, environment DSN, source maps, releases/commits, traces sampling, PII scrubbing, alerts, ownership, test event.

## Zeabur

- Project/service mapping, source/image, gateway/domain, variables, volumes, health/readiness, resource limits, logs/metrics, SSH policy, restart policy, rollback image.

## Integration adapters

Composio, Pipedream, Slimtools, browser/computer agents, and MCP servers are adapters, not sources of truth. Record connection owner, scopes, environment, last validation, and revocation path.
