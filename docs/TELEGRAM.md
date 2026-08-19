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
