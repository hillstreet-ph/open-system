# Open Notify and portfolio readiness

Open Notify uses the existing provider-managed credential `TELEGRAM_PROJECT_BOT_TOKEN`
(or `OPEN_NOTIFY_BOT_TOKEN`) and verifies bot identity 8902902175. Never store
the credential in this repository, a knowledge record, an issue, or a log.

| Project | Topic | Evidence on 2026-10-10 |
| --- | --- | --- |
| Open-System | 185 | Message 246, exact chat/thread verified |
| Open-Box | 186 | Message 247, exact chat/thread verified |
| Open-Connect | 187 | Message 248, exact chat/thread verified |
| Open-TGate | 188 | Message 249, exact chat/thread verified |
| Open-Teleset | 189 | Message 250, exact chat/thread verified |

These are existing topics in HillStreet Workspace, chat -1004449684934.
They are operational destinations. No broadcast or fallback to another topic
is permitted. KobePlay has no approved notification route in this five-topic
request; its restricted finance, staff, credentials and margin records must
stay in their existing restricted sources.

## Delivery

```bash
python scripts/operations/open_notify.py --home /opt/data \
  --project open-system --event-key deploy:COMMIT_SHA \
  --summary "Deployment validation completed; see the linked GitHub run."
```

Use a real source/run identifier for the event key. The same key and payload
sends once within the retained 500-event ledger. Reusing a key for different
content returns a conflict. Explicit Telegram 429 responses defer and retry
at most three times; respect retry_after. Timeout, interrupted delivery,
wrong destination and server errors remain uncertain and are never blindly
resent. Inspect Telegram and the private ledger before resolving uncertainty.

Credential-like text is rejected; callers must supply only approved operational
or client-safe summaries. The code does not infer data classification from
natural language. Private record content is never an acceptable summary.
The local ledger stores fingerprints and delivery metadata, not message text.

## Runtime monitoring

```bash
python scripts/operations/open_notify.py --home /opt/data --reconcile \
  --config config/open-system-portfolio.json
```

The monitor performs bounded public HTTP probes and reads existing scheduler
status. It reports observations, including runtime-local 403s, without claiming
full authentication, deployment or backup verification. It does not restart
services, rotate credentials, clean storage, mutate business data or repair
production. Use the existing self-healing/maintenance schedule as the invocation
point rather than adding a competing worker.

Run runtime project/Kanban administration as Hermes uid/gid 10000 with
HERMES_HOME=/opt/data. Preserve the existing volume and startup entrypoint.
Validate this module before installing a copy under /opt/data/scripts.
Keep a rollback copy of any replaced runtime notification helper.

## One brain with separate sources

`config/open-system-portfolio.json` maps the six existing Open-Connect
projects to source repositories, canonical schema ownership and notification
topics. It is a source-linked catalog, not proof that every described database
object exists. Open-System execution state remains in its existing Hermes
stores and Open-Platform boundary. Open-KobePlay/Open-TGate/Open-Teleset retain
their Open-Operations boundaries. Open-Box owns artifacts and knowledge-source
references. Open-Connect owns connection grants and credential references.

Knowledge records require organization/project/source IDs, version, owner,
visibility and timestamps. Query through authorized project-scoped APIs;
never merge plaintext secrets or restricted client data into global memory.
The existing schema split is tracked in open-system issue #39; this change
does not migrate or rename any database object.

## Current integration limits

ChatGPT Open-Connect, Composio GitHub and Open-TGate read tools succeeded.
Zeabur authenticated runtime execution succeeded. A direct authenticated
Open-System request to https://open-connect.site/mcp returned HTTP 403.
Do not route the same credential elsewhere to bypass an enforced restriction.
Resolve the authorized origin/access contract and repeat tool discovery before
claiming runtime connector execution. Composio accounts and ChatGPT plugin
installations are separate from runtime authorization.

Legacy configuration strings such as /v1/chatgpt/brain are unverified and must
not be treated as deployed APIs. Reuse the verified Open-Connect MCP endpoint.
A database blueprint, connector record or cron manifest is not an installed
executor or functioning schedule.

For autonomy, use real Hermes approval keys: approvals.mode, cron_mode,
single_query_mode and smart_policy. Values such as cron_mode=auto and
auto_approve_deployments are not read by the current approval contract.
Use automatic routine decisions with a bounded smart policy and honor
provider-enforced approvals. GitHub changes still require issue locks,
tests, reviews and exact-head checks. Cap repair at three attempts.

## Validation

Sixteen regression tests cover exact thread routing, deduplication, changed-content
conflicts, timeout uncertainty, wrong-thread uncertainty, bounded 429 retries,
restricted/unknown destinations, credential rejection, fingerprint-only storage
bot identity, injected environment credentials, fine-grained PAT rejection,
legacy/BOM scheduler state, provider-token families, UTF-16 message limits
and Windows lock contention beyond ten seconds. Run:

```bash
python tests/unit/test_open_notify.py
```

Live delivery evidence verifies notification transport only. It does not prove
all integrations, encrypted restores, or production readiness.


Verified database boundary repair is tracked in [OpenBox #41](https://github.com/hillstreet-ph/open-box/issues/41). Canonical schemas and active legacy public tables are distinct; preserve source records until migration and grants are verified. Supabase catalog metadata is evidence of existing storage, not proof of a working global knowledge search. Runtime smart approval handles routine commands; unresolved unattended escalation remains denied. The existing hourly ChatGPT automation is enabled with bounded project-scoped work and no credential rotation.
