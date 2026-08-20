# Multi-agent, parallel, sub-agents

Profiles: admin-agent, ops-agent, dev-agent, research-agent, public-agent.

Teams in Supabase `open_system_agent_teams`:
- ops-core (lead ops-agent, parallel_max 4)
- product-dev (lead dev-agent, parallel_max 3)

Runtime: Hermes `delegate_task` for sub-agents; `open_system_job_queue` for parallel jobs.
