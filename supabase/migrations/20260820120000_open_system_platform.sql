-- Open-System platform tables (idempotent). Does NOT drop or truncate existing data.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Deployment / image pin registry (synced from GitHub Actions metadata)
CREATE TABLE IF NOT EXISTS public.open_system_deployments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  git_sha text,
  image_ref text,
  image_digest text,
  environment text NOT NULL DEFAULT 'production',
  status text NOT NULL DEFAULT 'recorded',
  notes text
);

CREATE TABLE IF NOT EXISTS public.open_system_sync_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  source text NOT NULL, -- github | supabase | zeabur | manual
  event_type text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.open_system_agents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  slug text NOT NULL UNIQUE,
  display_name text,
  profile text NOT NULL DEFAULT 'default',
  model_provider text,
  system_prompt text,
  allowed_skills jsonb NOT NULL DEFAULT '[]'::jsonb,
  allowed_tools jsonb NOT NULL DEFAULT '[]'::jsonb,
  permission_profile text NOT NULL DEFAULT 'public-agent',
  enabled boolean NOT NULL DEFAULT true
);

-- Extend telegram routes if missing columns (safe)
CREATE TABLE IF NOT EXISTS public.open_system_telegram_routes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id text NOT NULL,
  thread_id text,
  agent_profile text NOT NULL DEFAULT 'default',
  enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (chat_id, thread_id)
);

CREATE TABLE IF NOT EXISTS public.open_system_audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  actor text,
  action text NOT NULL,
  resource text,
  detail jsonb NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS public.open_system_system_settings (
  key text PRIMARY KEY,
  value jsonb NOT NULL DEFAULT '{}'::jsonb,
  updated_at timestamptz NOT NULL DEFAULT now()
);

-- Backup catalog may already exist from earlier migration
CREATE TABLE IF NOT EXISTS public.open_system_backup_catalog (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  backup_id text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  git_sha text,
  image_digest text,
  verification_status text NOT NULL DEFAULT 'UNVERIFIED',
  notes text,
  storage_uri text,
  checksum_sha256 text
);

CREATE INDEX IF NOT EXISTS idx_open_system_sync_events_created
  ON public.open_system_sync_events (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_open_system_deployments_created
  ON public.open_system_deployments (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_open_system_audit_created
  ON public.open_system_audit_events (created_at DESC);

-- Optional: schedule via Supabase Dashboard → Database → Extensions → pg_cron
-- SELECT cron.schedule('open-system-backup-reminder', '0 6 * * *', $$
--   INSERT INTO public.open_system_sync_events(source, event_type, payload)
--   VALUES ('supabase', 'backup_reminder', '{"msg":"run external backup"}'::jsonb);
-- $$);
