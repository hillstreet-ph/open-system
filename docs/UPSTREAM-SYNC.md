# Upstream Hermes synchronization

Workflow: `.github/workflows/upstream-sync.yml`

- Scheduled + `workflow_dispatch`
- Creates/updates `upstream-sync/*` branch
- Opens PR against `main`
- **Never** force-pushes `main`
- **Never** auto-merges to production

## Review checklist (every upstream PR)

- [ ] CI green (Open-System required checks)
- [ ] `docker-release.yml` / ops scripts / docs still present
- [ ] Dockerfile ENTRYPOINT/CMD reviewed
- [ ] New/removed env vars noted
- [ ] No secrets introduced
- [ ] `/opt/data` contract intact

## Compatibility report

CI may write `artifacts/upstream-compatibility.json` on sync PRs (when workflow enabled).


## Stable reconciliation: 2026-10-01 (issue #37)

Target: Hermes v0.21.5 (`v2026.9.24`), commit
`f97608f178d1ffeca59860195ab7da295f7c8e5f`. Fork baseline:
`9def663c2eb7907c68aa1e0839ed82f7d5df0b8f`. The release is a bounded
upstream target; it is not an unreviewed merge of moving upstream main.

The older `upstream-sync/main-fdf6f1d` branch is already an ancestor of
the fork baseline. The `main-dbbd893` target is an ancestor of this
release; its historical merge branch is retained, not force-updated.

### Conflict decisions

The stable merge produced 32 unmerged paths:

- `.env.example`: retain both upstream examples and the Open-System production contract.
- `AGENTS.md`: retain HillStreet governance and canonical protocol routing.
- `pyproject.toml`, `tools/lazy_deps.py`: adopt upstream plugin/dependency
  changes, retaining the fork's patched `httpx2==2.12.0` in every matching extra.
- `package-lock.json`: regenerate from merged manifests, retaining the
  fork's Electron/Vitest upgrades rather than splicing generated JSON.
- `.github/workflows/osv-scanner.yml`: retain SARIF review-status reporting
  and the fork's Node-compatible artifact action.
- `.github/workflows/install-e2e.yml`, `install-e2e-run.yml`: adopt upstream
  multi-OS matrix and validated inputs; retain explicit no-release skips
  using the existing sentinel, propagated to all three OS runners.
- 24 file-location conflicts for HillStreet operations documents: retain
  original `docs/` paths and byte-identical contents, preserving existing
  external links and deployment references rather than automatically moving
  them under the upstream website. This document adds the reconciliation record.

Docker merged without conflict. The fork-only tunnel build stage, binary,
s6 service and opt-in behavior remain. Upstream's `/opt/data`,
`entrypoint-dispatch.sh` and `main-wrapper.sh` contracts remain compatible
with the installed persistence guard. Supabase migrations, integration
manifest, backup and recovery scripts are preserved; no database migration
is authorized by this merge itself.

### Validation and promotion

Initial targeted tests: 182 passed, 1 skipped, 1 failed because this local
workspace denies AF_UNIX socket creation. The failing upstream backup test
is retained unchanged and must run in CI. `uv lock --check`, frozen dev
sync, `npm ci --ignore-scripts`, and workflow YAML parsing succeeded.
Independent review found a macOS workflow condition formatting error,
which was corrected and rechecked; no additional merge-specific blocker
was identified. This is not a production approval.

Initial npm audit reports 10 vulnerabilities; address and re-audit before
promotion. Exact-head CI, security analysis, Docker build, immutable
digest, restored-volume staging, and verified SQLite-aware recovery
evidence remain mandatory. Existing shell tar verification alone does
not prove SQLite consistency. Preserve the current image and volume until
all gates pass; never reset runtime state to complete an upgrade.
