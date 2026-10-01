# Codex and central portfolio onboarding

This adapter extends the existing Hermes Kanban implementation for `open-system`,
`open-connect`, `open-box`, `open-tgate`, and `open-teleset`. It creates no new
application schema, credential registry, orchestration service, or scheduler.
`config/hillstreet-integrations.yaml` remains the integration contract.

## Prepare the repository

Use the issue-scoped branch and repository root as the Codex project directory.
Python must satisfy `pyproject.toml` (3.11–3.13); install Astral uv through its
official distribution, then run:

```sh
./scripts/codex-setup.sh --install
./scripts/codex-setup.sh --check
.venv/bin/python -m pytest tests/hermes_cli/test_portfolio.py -q
```

Installation uses `uv sync --locked --extra dev`, preserving the real dependency
lock and failing if it is stale. Optional provider extras are installed only when
needed. This does not install or authenticate the Codex service itself. Codex
cloud repository authorization, environment registration and a successful task
launch must be verified separately; repository scripts cannot repair cloud
executor registration errors.

## Preview and apply boards

Set `HERMES_HOME` to the existing persistent Hermes root on the target host. Do
not point production at a scratch checkout. The default command is read-only:

```sh
.venv/bin/python -m hermes_cli.portfolio
.venv/bin/python -m hermes_cli.portfolio --apply
```

The second command creates missing native boards only. Existing board metadata,
archives, tasks, credentials, current-board selection and workdirs are preserved.
Run onboarding from one administrative process; it is retry-idempotent, not a
replacement for deployment concurrency control. Worker-pinned `HERMES_KANBAN_DB`,
`HERMES_KANBAN_BOARD` and delegated-child contexts are rejected. In particular,
the native DB override would otherwise force all boards into one database.

## Goal intake and role routing

Create a UTF-8 goal file containing acceptance criteria and source references,
without secrets. Supply an explicit project and category; the adapter does not
guess ownership of collected data. Categories are `engineering`, `business`,
`agency`, and `data`.

```sh
.venv/bin/python -m hermes_cli.portfolio \
  --project open-system --category engineering \
  --goal-file /path/to/approved-goal.md --request-id github-issue-45
```

The preview lists project-scoped coordinator and specialist profile names. Apply
fails closed unless every required dedicated profile has `config.yaml`, and the
board has an existing absolute `default_workdir` that is a Git repository root
whose origin matches `hillstreet-ph/<project>` on GitHub. Profile symlinks,
missing profiles, missing workdirs and mismatched project origins are rejected
before a task is created. Existing native `project_id` links require explicit
routing reconciliation before this adapter accepts intake.

Configure profiles through native Hermes profile management, and set the board
workdir through `hermes kanban boards set-default-workdir`. Only then add
`--apply` to record a native **blocked** task with an atomic explicit block
event and `needs_input` reason. Native readiness recomputation preserves this
sticky block until explicit unblocking. It is never created in ready or
triage, so automatic triage decomposition cannot dispatch it via the default
profile. After reviewing credentials, profile permissions, worktree support,
budgets and source access, explicitly unblock through the native Kanban workflow.
Unblocking is the activation step, and a live dispatcher may immediately run the
task. An external automation that unblocks tasks must honor this review gate.

Reusing the request ID returns the existing active task rather than creating a
duplicate; this is native Kanban deduplication, not a permanent event ledger for
archived tasks. A category correction under the same request ID requires editing
the existing task through the native workflow. Missing or archived boards fail
closed. Goal text is stored only in the selected project's native board.

Profile routing targets use `<project>-<category>-<role>`:

| Category | Required roles |
| --- | --- |
| engineering | coordinator, developer, reviewer, qa |
| business | coordinator, operations, reviewer |
| agency | coordinator, service-provider, reviewer |
| data | coordinator, data-organizer, reviewer |

Names are routing targets, not provisioned agents. Use existing Hermes profile
management and native Kanban decomposition/swarm APIs to configure specialist
profiles and reviewed task graphs. Do not clone a credential-bearing profile to
populate a team. The adapter intentionally does not create model accounts,
copy credentials, start a dispatcher, activate a swarm, or promote tasks.

## Persistent operation and isolation

Native boards live under `<Hermes root>/kanban/boards/<project>/`, each with its
own SQLite DB, metadata, logs and workspaces. Keep the existing Hermes root,
profiles, memory, configuration and board data on durable mounted storage across
redeploys. Back up SQLite using its backup API or a coordinated stopped service
snapshot; copying a live DB without its WAL can lose committed work. Test restore
on a separate host before claiming recovery readiness. This change does not
install a backup schedule or verify the existing production volume.

Operate one dispatcher authority for a shared Hermes root. The native gateway
can sweep all boards; do not additionally start a standalone dispatcher against
the same state. Use native board pinning for workers. Boards separate task state;
they are not an operating-system or tenant security boundary. Constrain worker
filesystem mounts, provider scopes, profile memory, knowledge retrieval filters
and network capabilities per project. Client-safe agency outputs must never
include internal costs or owner-only knowledge. Ambiguous collected records stay
in intake until a source owner/project is established; preserve source IDs and
access classifications when organizing data.

## Activation evidence still required

Before unattended work, verify the five repository authorizations and Codex
launches; durable mounts and restore evidence; selected model/gateway access;
project-specific profiles and tool permissions; runtime budgets/retry limits;
GitHub issue locks and independent reviewer/QA roles; and one healthy dispatcher.
Use Proton Pass or the existing provider secret broker for minimum-scope secrets.
No secret values belong in goals, code, logs, issue bodies or artifacts.

Review and CI precede merge/release; staging health and rollback evidence precede
production deployment under the shared development protocol. This onboarding
change alone is not evidence that any deployment or autonomous team is active.
