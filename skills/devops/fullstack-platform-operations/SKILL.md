---
name: fullstack-platform-operations
description: "Operate a secure full-stack delivery platform end to end."
version: 0.1.0
author: HillStreet Information Technology Services
license: MIT
platforms: [linux, macos, windows]
---

# Full-Stack Platform Operations

Build and operate a reproducible delivery path:

`GitHub -> CI/security -> Docker Hub -> Cloudflare/Supabase -> Zeabur -> Sentry -> verification`

Treat the repository and provider APIs as the source of truth. Never infer that configuration is complete from documentation alone.

## Operating contract

- Preserve user changes and inspect before editing.
- Never place secret values in source, logs, artifacts, prompts, or the packaged toolkit.
- Replace Railway only after identifying every reference, mapping the Zeabur replacement, and validating rollback.
- Use least-privilege credentials and separate development, staging, and production.
- Autonomous repair is bounded: diagnose, branch, patch, test, open/update a PR, and stop after three failed repair cycles.
- Require explicit authorization immediately before destructive production changes, credential rotation, DNS cutover, database migrations, or irreversible deletion.
- Never promise “zero bugs.” Report verified results, residual risks, and blocked checks.

## Workflow

1. Inventory repositories, services, domains, environments, data stores, workflows, secrets by name, and ownership. Run `scripts/audit-platform.sh <repo>` for a local baseline.
2. Classify findings as confirmed, inferred, missing, conflict, or secret-required. Do not print secret values.
3. Read [references/architecture.md](references/architecture.md) for platform boundaries and [references/provider-matrix.md](references/provider-matrix.md) for provider-specific checks.
4. For Railway removal, read [references/migration.md](references/migration.md). Produce a mapping before edits.
5. For credentials or connectors, read [references/secrets-and-connections.md](references/secrets-and-connections.md). Validate identity, scope, environment, and expiration without exposing values.
6. Apply the smallest reversible change set. Use templates in `assets/starter/` only after adapting them to the project’s language, build, test, and runtime commands.
7. Validate locally, in CI, in staging, then at the public boundary. Confirm health, logs, rollback, Sentry release visibility, and the deployed image digest.
8. Report an evidence matrix: check, environment, result, evidence, owner, and follow-up.

## Delivery gates

A release may progress only when lint/type/unit/integration tests, dependency and secret scans, container build, migration safety checks, and staging smoke tests pass. Production requires a protected environment or equivalent approval, an immutable image digest, a rollback target, and post-deploy health verification.

## Cross-agent portability

Use `scripts/install-agent-skill.sh <target> [install-root]` to install this skill for `chatgpt`, `claude`, `codex`, `open-connect`, or `generic`. The script copies instructions only; it does not install plugins, grant account access, or copy credentials. Connectors remain platform-specific and must be authorized in each agent’s UI or MCP configuration.

When a named connector is unavailable, generate the exact connection checklist and mark execution blocked rather than claiming completion.
