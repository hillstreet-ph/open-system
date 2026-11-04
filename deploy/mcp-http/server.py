#!/usr/bin/env python3
"""Authenticated HTTP front for the Hermes MCP server (mcp.open-system.space).

`hermes mcp-serve` speaks MCP over stdio only. This process starts it as a child and
re-exposes it over Streamable HTTP (`/mcp`) and SSE (`/sse`) for remote MCP clients.

Every request except `GET /healthz` must carry `Authorization: Bearer <MCP_HTTP_TOKEN>`.
The process refuses to start without a token of at least 32 characters, so the bridge
can never come up unauthenticated. If the stdio child exits, the process exits non-zero
and s6 restarts it.
"""
from __future__ import annotations

import asyncio
import hmac
import logging
import os
import shlex
import sys

import uvicorn
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters
from mcp_proxy.mcp_server import _StdioExitWatch, create_single_instance_routes
from mcp_proxy.proxy_server import create_proxy_server
from starlette.applications import Starlette

log = logging.getLogger("mcp-http")
OPEN_PATHS = frozenset({"/healthz"})


class BearerAuth:
    """Pure ASGI middleware: constant-time bearer check on every non-health request."""

    def __init__(self, app, token: str) -> None:
        self.app = app
        self.token = token.encode()

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or scope.get("path") in OPEN_PATHS:
            await self.app(scope, receive, send)
            return
        header = b""
        for key, value in scope.get("headers", []):
            if key == b"authorization":
                header = value
                break
        scheme, _, presented = header.partition(b" ")
        if scheme.lower() == b"bearer" and hmac.compare_digest(presented.strip(), self.token):
            await self.app(scope, receive, send)
            return
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"www-authenticate", b'Bearer realm="open-system-mcp"'),
            ],
        })
        await send({"type": "http.response.body", "body": b'{"error":"unauthorized"}'})


async def main() -> int:
    logging.basicConfig(level=os.environ.get("MCP_HTTP_LOG_LEVEL", "INFO"),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.environ.get("MCP_HTTP_TOKEN", "").strip()
    if len(token) < 32:
        log.error("MCP_HTTP_TOKEN missing or shorter than 32 characters; refusing to start")
        return 2

    argv = shlex.split(os.environ.get("MCP_HTTP_COMMAND", "hermes mcp-serve"))
    params = StdioServerParameters(command=argv[0], args=argv[1:], env=dict(os.environ))
    watch = _StdioExitWatch()
    async with watch.client(params, "hermes") as streams, ClientSession(*streams) as session:
        server = await create_proxy_server(session)
        routes, manager = create_single_instance_routes(server, stateless_instance=True)
        app = BearerAuth(Starlette(routes=routes), token)
        config = uvicorn.Config(
            app,
            host=os.environ.get("MCP_HTTP_HOST", "0.0.0.0"),
            port=int(os.environ.get("MCP_HTTP_PORT", "8765")),
            proxy_headers=True,
            forwarded_allow_ips="*",
            log_level="info",
        )
        http = uvicorn.Server(config)
        watch.attach(http)
        async with manager.run():
            log.info("serving %s on :%s (/mcp, /sse)", " ".join(argv), config.port)
            await http.serve()
    return 1 if watch.exited else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
