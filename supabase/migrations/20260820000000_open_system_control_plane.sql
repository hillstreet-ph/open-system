-- Open-System control-plane scaffolding (idempotent).
-- Does NOT drop existing objects. Safe to apply on empty or existing projects.

CREATE TABLE IF NOT EXISTS public.open_system_backup_catalog (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  backup_id text NOT NULL UNIQUE,
  created_at timestamptz NOT NULL DEFAULT now(),
  git_sha text,
  image_digest text,
  verification_status text NOT NULL DEFAULT 'UNVERIFIED',
  notes text
);

CREATE TABLE IF NOT EXISTS public.open_system_telegram_routes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  chat_id text NOT NULL,
  thread_id text,
  agent_profile text NOT NULL DEFAULT 'default',
  enabled boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (chat_id, thread_id)
);

-- RLS placeholders: enable and policies must be designed per org before public access.
-- ALTER TABLE public.open_system_backup_catalog ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE public.open_system_telegram_routes ENABLE ROW LEVEL SECURITY;
