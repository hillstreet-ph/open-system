# Reference architecture

| Layer | System | Responsibility | Required evidence |
|---|---|---|---|
| Source/control | GitHub | Code, reviews, workflows, releases | Protected branches, passing checks, traceable release |
| Artifact | Docker Hub | Immutable runtime images | Semantic tag plus digest and scan result |
| Edge | Cloudflare | DNS, TLS, WAF, Pages/Workers, caching | Active zone, correct records, TLS and WAF checks |
| Data | Supabase | Postgres, Auth, Storage, Realtime, Edge Functions, Vector | Project ref, migrations, RLS tests, backup/restore evidence |
| Runtime | Zeabur | Services, gateway, volumes, environment, health | Service mapping, image digest, health and rollback |
| Observability | Sentry | Errors, traces, releases, alerts | DSN by environment, release association, test event |

Maintain `development`, `staging`, and `production` as distinct trust zones. Give each its own Supabase strategy, Sentry environment, Zeabur configuration, Cloudflare routing, and secret set.

Each repository should expose a machine-readable `platform.yaml` or equivalent containing non-secret identifiers: project name, owners, build/test commands, Docker image, Cloudflare resources, Supabase alias, Sentry slug, Zeabur project/service, domains, health endpoint, migrations command, and rollback command.

Use one release identifier across Git tag, container labels, Sentry release, and deployment metadata. Prefer semantic version plus commit SHA and deploy by digest in production.
