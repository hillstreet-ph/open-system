# Security

- No secrets in Git or workflow logs
- Least-privilege GitHub Actions permissions
- CodeQL / dependency scanning (upstream workflows)
- Dashboard: auth required on non-loopback binds
- API: bearer key required
- Telegram: user allowlist
- Backups: encrypt at rest when offsite
- Service-role Supabase key: server only

## Branch protection (owner action)

On `main`:

- Require PR
- Require status checks that are stable (CI aggregate, CodeQL)
- Block force-push and deletion
- Do not require dynamic matrix job names that cannot be configured
