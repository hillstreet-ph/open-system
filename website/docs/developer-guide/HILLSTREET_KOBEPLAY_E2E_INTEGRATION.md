# HillStreet + KobePlay end-to-end integration runbook

Issue: #41

## Architecture

ChatGPT connects to the Open-Connect MCP gateway. Open-Connect owns identity,
scopes, connections, resources, models, policy, and audit. It delegates approved
execution to Open-System/Hermes. Open-TGate owns Telegram bot/account/group/topic
routing. Open-System must not receive raw provider credentials in prompts.

```text
ChatGPT -> open-connect.site/mcp -> Open-Connect policy/audit
                                      |
                                      v
                              Open-System/Hermes
                                      |
                    +-----------------+-----------------+
                    |                 |                 |
                 Open-TGate        Airtable/Notion   GitHub/Supabase
                    |
          HillStreet and KobePlay Telegram workspaces
```

This is an internal tool-only ChatGPT app. A custom widget is not required.
Every read-only tool must be callable without UI. Mutating tools must accurately
declare their risk and require confirmation where applicable.

## Organization boundaries

| Organization | Default visibility | Primary workflows |
|---|---|---|
| HillStreet | Internal | Development, business operations, agency services, data engineering, owner-only personal operations |
| KobePlay | Client-safe by default | Business operations, development, influencer marketing, agent marketing, reporting |

Never copy HillStreet internal pricing, staff private data, credentials, or
agency margins into KobePlay client-visible knowledge.

## Primary system of record

| Capability | Primary system | Notes |
|---|---|---|
| Source, issues, releases, deployment evidence | GitHub | One issue and branch per change |
| Connection policy and MCP | Open-Connect | External AI clients enter here |
| Agent execution | Open-System | Planner, workers, reviewer, schedules |
| Telegram | Open-TGate | One multi-bot router; chat/topic allowlist |
| Structured operations | Airtable | Operational records and workflow registry |
| SOPs and reviewed knowledge | Notion | No raw secrets or sensitive staff fields |
| Files and source references | Google Drive | Link/source IDs instead of duplicate uploads |
| Database and auth | Supabase | open-platform and open-operations |
| Runtime | Zeabur | Secrets injected outside Git |
| Edge | Cloudflare | DNS, TLS, WAF, rate limiting |
| Errors and releases | Sentry | Environment and release correlation |

Connector priority: native provider connector, then Composio, then Slim.tools,
then Pipedream. Do not connect one provider through every adapter.

## ChatGPT app connection

Use the stable HTTPS MCP URL:

```text
https://open-connect.site/mcp
```

Open-System remains the execution target and is not advertised as the public
control-plane MCP gateway.

Required minimum scopes:

- `openid`
- `mcp:connect`
- `resources:read`
- `models:read`
- `models:invoke`

Write and production tools must use separate narrowly scoped permissions.

Current Open-Connect evidence: 85 published resources, one connected connection,
and five model aliases. This does not prove each provider connection is ready.

## Telegram route contract

Open-TGate must discover and persist verified chat and topic IDs before routes
can be enabled. Names and screenshots are not sufficient identifiers.

Recommended topics in each workspace:

1. 00 Command Center
2. 01 Development
3. 02 Business Operations
4. 03 Agency Services
5. 04 Data Engineering
6. 05 Alerts & Incidents
7. 06 Approvals
8. 07 Reports
9. 08 AI Agent Logs
10. 09 Personal — HillStreet owner only

Route key:

```text
organization_id:workspace_id:chat_id:topic_id
```

Every route must specify organization, visibility, project/domain, allowed
senders, agent, allowed actions, approval policy, and response destination.

The two bot tokens previously visible in screenshots are not valid deployment
inputs. Existing tokens are not deleted by this change, but exposed values must
not be consumed by production.

## Memory and knowledge

1. Session memory: temporary execution context.
2. Project memory: task decisions, artifacts, source links, and status.
3. Reviewed organization knowledge: approved SOPs, goals, policies, and history.

Promotion from project memory to organization knowledge requires review and a
source link. Never store private keys, tokens, passwords, service-role keys, raw
finance data, or private staff contact details in memory.

## Skills

Safe reusable skills may be installed after secret and private-data scanning:

- Open Influencer Organize — KobePlay influencer list consolidation.
- Business English Conversation Helper — professional team/client messaging.
- Organizing Numbered Year/Month Files — deterministic Drive organization.
- Full-Stack Platform Operations — delivery and provider validation.

Private account names and local paths must be replaced with role labels or
repo-relative paths before publication.

## Deployment sequence

1. Run `hermes doctor` in the Zeabur Open-System service and preserve redacted evidence.
2. Validate the environment names in
   `deploy/zeabur/open-system-integrations.env.example`.
3. Configure secrets only in Zeabur/provider stores.
4. Verify Open-Connect OAuth/MCP protected-resource metadata and scope enforcement.
5. Validate Open-System health, API origin, queues, retry/dead-letter behavior, memory, and audit.
6. Sync Open-TGate, verify both Telegram bots/accounts, and discover chat/topic IDs.
7. Add allowlisted development routes first.
8. Run read-only smoke tests for GitHub, Supabase, Notion, Airtable, and Drive.
9. Run one reversible Telegram test per organization.
10. Deploy staging by immutable image digest and run E2E tests.
11. Require explicit approval before production promotion.
12. Verify health, logs, Sentry release, audit records, and rollback digest.

## Current blockers

- Live Open-System admin/API/SSH evidence is not available to this agent.
- Open-TGate currently has no synchronized Telegram entities, so chat/topic IDs
  cannot be safely inferred.
- Supabase security advisors report privileged-function permission warnings.
  Open-platform also reports RLS-enabled tables without policies.
- The secret-manager path is not connected through Composio.
- Databricks workspace, catalog, compute policy, and data classification remain
  unconfirmed.

Do not claim production completion until these blockers are resolved and all
acceptance tests below pass.

## Acceptance tests

- ChatGPT authenticates to Open-Connect and lists only scoped tools/resources.
- Open-Connect delegates one read-only task to Open-System and records audit evidence.
- HillStreet and KobePlay Telegram routes cannot cross organizations.
- Unknown chats/topics/senders are denied.
- Notion, Airtable, Drive, GitHub, and Supabase pass safe read-only probes.
- Mutating tools request confirmation and write to the correct organization.
- No secret appears in Git, logs, model-visible results, Drive registers, or memory.
- CI, secret scan, container build, staging smoke/E2E, and rollback checks pass.
