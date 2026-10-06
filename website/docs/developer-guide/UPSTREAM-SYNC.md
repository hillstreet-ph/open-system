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
