# MCP connections (Notion, Drive, Sheets, Dropbox, OneDrive)

Registry: Supabase `open_system_mcp_connections` (enabled=false until secrets exist).

1. Create provider credentials.
2. Put secret **names** in Zeabur + GitHub secrets (values never in Git).
3. Merge blocks from `mcp.servers.example.json` into Hermes MCP config under HERMES_HOME.
4. Set `enabled=true` on the matching Supabase row.
5. Restart hermes-agent.

| Slug | Env secret names |
|------|------------------|
| notion | NOTION_API_KEY |
| gdrive | GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN |
| gsheets / gdocs | GOOGLE_SERVICE_ACCOUNT_JSON |
| dropbox | DROPBOX_ACCESS_TOKEN |
| onedrive | MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_TENANT_ID |
| github | GITHUB_PERSONAL_ACCESS_TOKEN |
