CREATE TABLE IF NOT EXISTS public.open_system_knowledge_collections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  slug text NOT NULL UNIQUE,
  title text NOT NULL,
  description text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS public.open_system_knowledge_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  collection_id uuid REFERENCES public.open_system_knowledge_collections(id) ON DELETE CASCADE,
  source_uri text,
  title text,
  content text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb
);
CREATE TABLE IF NOT EXISTS public.open_system_agent_teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  slug text NOT NULL UNIQUE,
  title text NOT NULL,
  lead_profile text NOT NULL DEFAULT 'ops-agent',
  member_profiles jsonb NOT NULL DEFAULT '[]'::jsonb,
  parallel_max int NOT NULL DEFAULT 4,
  enabled boolean NOT NULL DEFAULT true
);
CREATE TABLE IF NOT EXISTS public.open_system_mcp_connections (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now(),
  slug text NOT NULL UNIQUE,
  provider text NOT NULL,
  transport text NOT NULL DEFAULT 'stdio',
  command_hint text,
  env_secret_names jsonb NOT NULL DEFAULT '[]'::jsonb,
  enabled boolean NOT NULL DEFAULT false,
  notes text
);
