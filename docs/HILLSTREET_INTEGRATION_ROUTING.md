# HillStreet integration and routing contract

Issue: #41  
Environment order: development → staging → production  
Control plane: Open-Connect  
Execution plane: Open-System / Hermes  
Telegram control: Open-TGate

This document defines the non-secret deployment contract for connecting HillStreet services to Open-System. It does not contain credentials, chat IDs, topic IDs, private keys, or customer data.

## 1. System boundaries

| Plane | System | Responsibility |
|---|---|---|
| Control | Open-Connect | Connections, authorization, project scopes, model routing, approvals, audit |
| Execution | Open-System | Planning, routing, workers, review, memory, cron, MCP and tool execution |
| Messaging | Open-TGate | Multiple Telegram bots, groups, forum topics, allowlists and delivery |
| Model | Open-Model | Approved inference endpoints, quotas, health and cost routing |
| Data/artifact | Open-Box | Files, artifacts, knowledge packages and backups |
| Secrets | Open-Secret / provider stores | Credential values and rotation |
| Operations | Airtable | Structured operational state |
| Governance | Notion | SOPs, decisions, training and reviewed knowledge |
| Engineering | GitHub | Issues, branches, PRs, CI/CD, releases and evidence |
| Analytics | Databricks | Unity Catalog, lineage, quality, jobs and governed analytics |

## 2. Telegram topology

The Hermes native gateway supports one `TELEGRAM_BOT_TOKEN` per gateway process. HillStreet has two bots, so Open-TGate is the canonical multi-bot router. A two-gateway fallback is allowed only if Open-TGate is unavailable and each instance has separate secrets, state, allowlists and delivery targets.

| Bot | Workspace | Allowed scope |
|---|---|---|
| `@open_system_bot` | HillStreet Workspace | Internal development, business operations, agency services, data engineering, approvals, alerts and agent status |
| `@kobeplay_bot` | Kobeplay Workspace | KobePlay client-safe and department operations |

TaskNotify may be used for one-way alerts, but it is not a command or operations bot.

### Security incident gate

The prior bot tokens appeared in an uploaded screenshot. They are revoked credentials and must never be reused. Replacement values must be stored only in Open-Secret, Open-Connect Vault, Zeabur protected variables or another approved provider secret store.

### Topic routing contract

Open-TGate resolves:

```text
bot identity + numeric chat ID + numeric topic ID
→ organization + workspace + project + data class
→ Open-System agent/workflow
→ approval policy
→ response destination
```

No route may fall back from a restricted/private topic to a client-visible topic.

Recommended HillStreet topics:

- 00 Command Center
- 01 Development
- 02 Business Operations
- 03 Agency Services
- 04 Data Engineering
- 05 Alerts & Incidents
- 06 Approvals
- 07 Reports
- 08 AI Agent Logs
- 09 Personal — owner only

KobePlay topics must follow the existing department structure. Finance, internal margin, credentials, staff personal data and private operations never enter client-visible topics.

## 3. Connector policy

Use exactly one primary path per provider:

| Provider | Primary path | Fallback | Minimum boundary |
|---|---|---|---|
| GitHub | Official GitHub App/MCP | Open GitHub Kit | Repository-scoped permissions |
| Notion | Official Notion MCP | Composio | Approved workspace/pages only |
| Airtable | Official Airtable OAuth app | Composio | Named bases/tables only |
| Telegram | Open-TGate + Bot API | Isolated Hermes gateway | Approved bots/chats/topics only |
| Databricks | Open Databricks Kit/API | Open DevApps Kit | Workspace/catalog/schema and compute policy |
| ChatGPT | Open-Connect integration + scoped API key | Custom MCP | Project/resource scopes only |

Do not connect one provider simultaneously through Native, Composio, Slim.tools and Pipedream.

## 4. Open-System non-secret environment contract

Existing Hermes variables remain authoritative:

```dotenv
# Native single-bot fallback only. Do not set when Open-TGate is the active router.
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=
TELEGRAM_HOME_CHANNEL=
TELEGRAM_HOME_CHANNEL_NAME=
TELEGRAM_CRON_THREAD_ID=
TELEGRAM_WEBHOOK_URL=
TELEGRAM_WEBHOOK_PORT=
TELEGRAM_WEBHOOK_SECRET=

# GitHub
GITHUB_TOKEN=
GITHUB_APP_ID=
GITHUB_APP_PRIVATE_KEY_PATH=
GITHUB_APP_INSTALLATION_ID=

# Existing Open-System control/data plane
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
DATABASE_URL=
```

Deployment-specific Open-Connect/Open-TGate endpoint names must be implemented only after the live services expose their reviewed interface. Do not invent endpoint or token names in production.

## 5. Data ownership and synchronization

- GitHub is authoritative for code, issues, PRs, checks, releases and deployment evidence.
- Airtable is authoritative for structured business records and workflow state.
- Notion is authoritative for human-readable governance, SOPs, training and reviewed knowledge.
- Databricks is authoritative for governed analytical tables, lineage and quality results.
- Open-Box is authoritative for files, artifacts and backups.
- Open-System memory stores execution context and learned preferences, not master business records.
- Cross-system records use stable source IDs and links. Sensitive values are not duplicated.

Required metadata:

```text
source_system
source_record_id
organization_id
workspace_id
project_id
department
owner
environment
data_class
status
priority
tags
created_at
updated_at
verified_at
lineage
retention_policy
```

## 6. Memory and knowledge policy

Memory layers:

1. Session memory: temporary execution context.
2. Task/project memory: approved decisions and project state.
3. Organization knowledge: reviewed, source-linked, reusable guidance.

Personal, client-private and internal memories are isolated. Credentials, private keys, payment credentials, raw customer data and unrestricted chat history must not enter general memory. Promote a repeated successful outcome to knowledge only after review and retain source, timestamp and owner.

## 7. Workflow routes

| Domain | Lifecycle | Agent chain | Approval gates |
|---|---|---|---|
| Development | request → plan → branch → test → review → merge → deploy → verify → learn | planner → dev/devops → QA/reviewer | Merge, production deployment, schema/security changes |
| Business operations | intake → classify → assign → execute → approve → report → archive | ops supervisor → department worker → reviewer | Finance, staff access, client publication |
| Personal operations | capture → prioritize → schedule → execute → reflect → memory | personal_ops_ai | External messages, purchases, account changes |
| Agency services | lead → qualify → proposal → approval → delivery → billing → renewal | agency_ops_ai → specialist → reviewer | Pricing, contracts, client communications, payments |
| Data engineering | ingest → validate → catalog → transform → quality → publish → monitor | data_engineer_ai → data_quality_ai → reviewer | Sources, production writes, schema, grants and paid compute |

## 8. Databricks gate

Before any Databricks write or paid compute, record and verify:

- workspace host and cloud;
- account/workspace and authorized principal;
- metastore;
- catalog and schema;
- environment;
- data classification;
- compute policy;
- development warehouse/cluster;
- grants and lineage requirements;
- cost limits and shutdown policy.

Use version-controlled Databricks Asset Bundles. Validate in development and deploy only through reviewed promotion gates.

## 9. ChatGPT/Open-Connect contract

ChatGPT connects to Open-Connect, not directly to unrestricted production systems. The generated API credential must be scoped to the operator's accessible projects/resources and must preserve approvals, audit and secret isolation. Open-System executes authorized work and returns status/evidence to Open-Connect.

## 10. Verification checklist

- [ ] Both exposed Telegram tokens revoked.
- [ ] Replacement tokens stored in protected runtime secret stores.
- [ ] Open-TGate has two bot identities with non-overlapping group allowlists.
- [ ] Numeric chat/topic IDs mapped without publishing them.
- [ ] Denial tests prove cross-workspace routing is blocked.
- [ ] Open-System `hermes doctor` passes.
- [ ] Open-System gateway/platform status is healthy.
- [ ] GitHub, Notion and Airtable MCP connections use least privilege.
- [ ] Databricks governance prerequisites are confirmed.
- [ ] Development E2E produces an audit record and evidence link.
- [ ] Staging smoke and failure/retry tests pass.
- [ ] Production promotion has explicit human approval.
- [ ] Rollback and last-known-good image digest are recorded.
