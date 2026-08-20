-- Default agent rows for Open-System (idempotent upsert by slug).

INSERT INTO public.open_system_agents (slug, display_name, profile, permission_profile, enabled)
VALUES
  ('admin-agent', 'Admin Agent', 'admin-agent', 'admin-agent', true),
  ('ops-agent', 'Ops Agent', 'ops-agent', 'ops-agent', true),
  ('research-agent', 'Research Agent', 'research-agent', 'research-agent', true),
  ('dev-agent', 'Developer Agent', 'dev-agent', 'dev-agent', true),
  ('public-agent', 'Public Agent', 'public-agent', 'public-agent', true)
ON CONFLICT (slug) DO UPDATE SET
  display_name = EXCLUDED.display_name,
  profile = EXCLUDED.profile,
  permission_profile = EXCLUDED.permission_profile,
  enabled = EXCLUDED.enabled,
  updated_at = now();
