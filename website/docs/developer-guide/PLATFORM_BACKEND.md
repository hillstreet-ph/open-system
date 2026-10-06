# Platform backend assignment

This repository is assigned to the shared **open-platform** Supabase project.

## Non-secret configuration

| Setting | Value |
|---|---|
| Supabase project | `open-platform` |
| Supabase project reference | `huadtiuuoiriqrjpjxhr` |
| Supabase URL | `https://huadtiuuoiriqrjpjxhr.supabase.co` |
| PostgreSQL schema | `open_system` |
| Sentry organization | `hillstreet` |
| Sentry project | `open-system` |
| GitHub repository | `hillstreet-ph/open-system` |
| Container image | `${DOCKERHUB_USERNAME}/open-system` |

## Required deployment secrets

Configure these only in GitHub environment secrets and the Zeabur service secret store:

- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_DB_URL` when server-side migrations or direct PostgreSQL access are required
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`
- `ZEABUR_API_KEY` only for deployment automation that requires it
- `SENTRY_AUTH_TOKEN` only for release/source-map upload
- Application-specific secrets

Public client builds may use the Supabase URL and publishable key. Never expose the service-role key, database password, Docker Hub token, Zeabur key, or Sentry auth token in source code, build logs, Google Drive, or client bundles.

## Deployment boundary

1. GitHub is the source of truth.
2. CI validates the project and builds a versioned container.
3. Docker Hub stores the approved image.
4. Zeabur deploys the approved immutable image.
5. Cloudflare provides DNS, TLS, WAF, and public routing.
6. Sentry records releases and runtime errors.
7. Supabase migrations must target schema `open_system` and must be reviewed before production execution.

## Current credential status

The previously shared Supabase, Docker Hub, and Zeabur management tokens were exposed in chat and must be rotated before write-enabled CI/CD or deployment is activated.
