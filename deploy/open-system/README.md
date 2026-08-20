# Open-System production enablement pack

Templates for multi-agent profiles and Telegram group routing.

## Install onto volume (Zeabur / VPS)

```bash
export HERMES_HOME=/opt/data
mkdir -p "$HERMES_HOME/profiles"
cp -R deploy/open-system/profiles/* "$HERMES_HOME/profiles/"
cp deploy/open-system/telegram/routes.example.yaml "$HERMES_HOME/telegram-routes.example.yaml"
# Edit chat IDs; keep secrets in platform env only
```

## Profiles

| Profile | Role |
|---------|------|
| admin-agent | Ops admin (allowlist only) |
| ops-agent | Status / operations |
| research-agent | Web / knowledge |
| dev-agent | Development assistance |
| public-agent | Safe public chat |

## Telegram multi-group

1. Create groups; add `@open_system_bot`
2. Get chat IDs
3. Fill `telegram-routes` / Supabase `open_system_telegram_routes`
4. Set `TELEGRAM_ALLOWED_USERS` for private DMs

## Models

Configure via env (recommended):

- `OPENROUTER_API_KEY` — multi-model gateway
- Or Zeabur AI Hub vars if provided by platform

There is **no free unlimited API key** in this repo. Use your provider accounts.

## Safety

Do **not** enable unrestricted host terminal for public Telegram groups.
