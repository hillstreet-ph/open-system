# Hermes MCP over HTTP (`mcp.open-system.space`)

`hermes mcp-serve` only speaks stdio. `server.py` runs it as a child process and serves it
over Streamable HTTP and SSE, behind a bearer token. It runs as the s6 service
`hermes-mcp-http` inside the production container and listens on port 8765. Railway routes
`mcp.open-system.space` to that port.

| Endpoint | Auth |
|---|---|
| `https://mcp.open-system.space/mcp` (Streamable HTTP) | `Authorization: Bearer $MCP_HTTP_TOKEN` |
| `https://mcp.open-system.space/sse` (legacy SSE) | same |
| `https://mcp.open-system.space/healthz` | none (returns 204) |

The token is the Railway service variable `MCP_HTTP_TOKEN`. The release workflow creates it
once with `deploy/railway.sh ensure-secret` and never prints it. Copy it from Railway →
`hermes-agent` → Variables. Without a token of at least 32 characters, the service stays
dormant (s6) or refuses to start (`server.py`).

Client example (Claude Code / Codex / any Streamable-HTTP MCP client):

```json
{ "mcpServers": { "open-system": {
    "type": "http", "url": "https://mcp.open-system.space/mcp",
    "headers": { "Authorization": "Bearer ${MCP_HTTP_TOKEN}" } } } }
```

Rotating: delete `MCP_HTTP_TOKEN` in Railway, then run the **Open-System release**
workflow with `deploy` enabled. A new token is generated, and every client must be updated.

## Dependencies

The bridge has its own venv at `/opt/mcp-http`. `mcp-proxy` needs `mcp<2`, while Hermes
ships `mcp` 2.x. `requirements.lock` is hash-pinned to the CPython 3.14 wheels used on
linux amd64/arm64. To regenerate it, run `pip-compile --generate-hashes requirements.txt`
inside the image. Then trim the hashes to the manylinux x86_64/aarch64, abi3 and
`py3-none-any` wheels.
