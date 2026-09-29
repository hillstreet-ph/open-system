# Railway-to-Zeabur migration

1. Find Railway references in code, workflows, docs, DNS, environment names, callback URLs, badges, and provider configs.
2. Inventory each service: source, command, port, health path, resources, volumes, variable names, dependencies, domains, cron jobs, and data.
3. Map every service to a Zeabur project/service or explicitly document consolidation.
4. Provision Zeabur without changing production DNS. Import secret values through the provider secret store.
5. Deploy the same immutable artifact, apply migrations once, and run smoke/integration checks.
6. Test backup and rollback. Lower DNS TTL before an approved cutover when applicable.
7. Cut traffic only after authorization; monitor errors, latency, saturation, and business checks.
8. Remove Railway from active automation after stability is confirmed. Delete provider resources only with explicit authorization.

Search for: `railway`, `RAILWAY_`, `railway.app`, `railway.json`, `railway.toml`, badges, callback URLs, and DNS targets.
