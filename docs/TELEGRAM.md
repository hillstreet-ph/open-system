# Telegram multi-agent routing (Open-System)

Hermes natively supports Telegram via `TELEGRAM_BOT_TOKEN`.

## Baseline (current)

```text
TELEGRAM_BOT_TOKEN=…
TELEGRAM_ALLOWED_USERS=<comma-separated numeric IDs>
HERMES_GATEWAY_BOOTSTRAP_STATE=running
```

Least privilege: allowlist users; do not open unrestricted terminal tools to public chats.

## Multi-agent goal (incremental)

| Route | Maps to |
|-------|---------|
| Group / topic A | Agent profile A (prompt, model, tools) |
| Group / topic B | Agent profile B |

Persist routes outside the image (volume config and/or Supabase tables) so container replacement does not lose routing.

Admin changes should not require source edits.

## Security

- Public-agent: no production shell, no secret filesystem
- Admin-agent: explicit allowlist only

## Multi-group routing (production)

Use profile templates under `deploy/open-system/profiles/` and the example
`deploy/open-system/telegram/routes.example.yaml`.

Persist durable routes in Supabase table `open_system_telegram_routes` after
migrations are applied (`docs/INTEGRATION.md`).

### Suggested mapping

| Group purpose | Profile |
|---------------|---------|
| Admin / ops | ops-agent or admin-agent |
| Research | research-agent |
| Public community | public-agent |
| Engineering | dev-agent |

Always set `TELEGRAM_ALLOWED_USERS` for DM access control.
