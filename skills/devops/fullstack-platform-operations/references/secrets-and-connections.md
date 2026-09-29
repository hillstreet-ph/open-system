# Secrets and connections

Record only: variable name, provider, purpose, environment, owner, consumer, scope, rotation date, expiry, validation status, and vault reference. Do not record secret values in reports or source files.

For each credential, verify authenticated identity, intended tenant/project, minimal scopes, environment, expiration, and one safe read-only operation. Redact tokens from output.

Standard names:

- `GITHUB_TOKEN` or OIDC configuration
- `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, server-only `SUPABASE_SERVICE_ROLE_KEY`
- `SENTRY_DSN`, `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT`
- `ZEABUR_TOKEN` and non-secret project/service identifiers

Map existing names instead of duplicating them blindly.

Connection states: `connected-validated`, `connected-unvalidated`, `authorization-required`, `scope-insufficient`, `wrong-tenant`, `expired`, or `not-configured`.
