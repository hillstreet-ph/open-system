# HillStreet AI Platform - GitHub Secrets & Environments Requirements

## Current State (Audited 2026-09-08)

### open-system (hillstreet-ph/open-system)

**Secrets (12 configured):**
| Secret | Status | Purpose |
|--------|--------|---------|
| DOCKERHUB_TOKEN | Configured | Docker Hub publish authentication |
| DOCKERHUB_USERNAME | Configured | Docker Hub publish username |
| ZEABUR_TOKEN | Configured | Zeabur deployment |
| SUPABASE_ACCESS_TOKEN | Configured | Supabase management API |
| SUPABASE_PROJECT_REF | Configured | Supabase project reference |
| SUPABASE_URL | Configured | Supabase API URL |
| SUPABASE_SERVICE_ROLE_KEY | Configured | Supabase service role |
| SUPABASE_JWT_SECRET | Configured | JWT verification |
| SUPABASE_DB_PASSWORD | Configured | Direct database access |
| DATABASE_URL | Configured | PostgreSQL connection string |
| OPENROUTER_API_KEY | Configured | AI model routing |
| BACKUP_S3_URI | Configured | Backup storage |

**Environments (3):**
- `gh-image`
- `Hermes Agent / production`
- `production`

**ACTION REQUIRED:**
- Create `container-publish` environment (referenced in new Docker workflow PR #12)
- OR update the workflow to use existing `production` environment

---

### open-connect (hillstreet-ph/open-connect)

**Secrets: NONE CONFIGURED**

**Environments: NONE CONFIGURED**

**ACTION REQUIRED - All secrets must added:**

| Secret | Required For | Priority |
|--------|-------------|----------|
| DOCKERHUB_TOKEN | Docker image publish (PR #24 workflow) | P0 |
| DOCKERHUB_USERNAME | Docker image publish (PR #24 workflow) | P0 |
| SUPABASE_ACCESS_TOKEN | Supabase management API | P0 |
| SUPABASE_PROJECT_REF | Value: gnqpwewbgldonarggzax | P0 |
| SUPABASE_URL | Supabase API endpoint | P0 |
| SUPABASE_SERVICE_ROLE_KEY | Server-side Supabase access | P0 |
| SUPABASE_JWT_SECRET | JWT token verification | P1 |
| ZEABUR_TOKEN | Zeabur deployment automation | P1 |

**Environments to create:**
- container-publish (for Docker workflow gating)
- production (for deployment workflows)

---

### open-box (hillstreet-ph/open-box)

**Secrets (17 configured):**
All required secrets are configured including DockerHub, Cloudflare, Zeabur, Supabase, OAuth.

**Environments (2):**
- Hermes Agent / production
- open-box / production

No immediate action required.
