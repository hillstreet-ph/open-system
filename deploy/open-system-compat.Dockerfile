# hermes-version: v0.22.7  (base = nousresearch/hermes-agent:v0.22.6, digest-pinned below)
FROM hillstreet/open-system@sha256:7d7620db45e9dce4c2a25a1f3bbd864531d9320391f4902090dbaf690e08fc25 AS legacy
FROM nousresearch/hermes-agent@sha256:e6d81ae52ebf6a43efa529701405509f20054ba818f179ddd748bed4f8af584c

# Retain the existing Open-System tunnel while upgrading Hermes itself.
COPY --from=legacy /usr/local/bin/tunnel-client /usr/local/bin/tunnel-client
COPY --from=legacy /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel
COPY --from=legacy /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-mcp-tunnel /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-mcp-tunnel

# These plugins moved out of core; Hermes PM resolves their dependencies.
ARG PLUGIN_COMMIT=6389dd08c1e485db708688c69e42c2b7a7360f4e
RUN set -eu; \
    mkdir -p /opt/hermes/plugins/mcp-serve /opt/hermes/plugins/spotify /opt/hermes/plugins/langfuse; \
    curl -fsSL --retry 3 "https://github.com/NousResearch/hermes-official-plugins/archive/${PLUGIN_COMMIT}.tar.gz" -o /tmp/mcp-plugin.tar.gz; \
    echo '34db1de3f19de74fd0ae59abc7976a339ea171c70fa9ce39e06296a89d520da2  /tmp/mcp-plugin.tar.gz' | sha256sum -c -; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/mcp-serve "hermes-official-plugins-${PLUGIN_COMMIT}/mcp-serve"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/spotify "hermes-official-plugins-${PLUGIN_COMMIT}/spotify"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/langfuse "hermes-official-plugins-${PLUGIN_COMMIT}/langfuse"; \
    rm /tmp/mcp-plugin.tar.gz; \
    sed -i 's/hermes mcp serve/hermes mcp-serve/' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run; \
    test -f /opt/hermes/plugins/mcp-serve/plugin.yaml; \
    test -f /opt/hermes/plugins/spotify/plugin.yaml; \
    test -f /opt/hermes/plugins/langfuse/plugin.yaml; \
    grep -q 'hermes mcp-serve' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run

# Authenticated HTTP bridge for the Hermes MCP server (mcp.open-system.space, port 8765).
# Separate venv: mcp-proxy needs mcp<2 while Hermes ships mcp 2.x. Dormant without MCP_HTTP_TOKEN.
COPY deploy/mcp-http/requirements.lock deploy/mcp-http/server.py /opt/mcp-http/
COPY deploy/mcp-http/run /etc/s6-overlay/s6-rc.d/hermes-mcp-http/run
RUN set -eu; \
    "$(readlink -f /opt/hermes/.venv/bin/python3)" -m venv /opt/mcp-http; \
    /opt/mcp-http/bin/pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/mcp-http/requirements.lock; \
    echo longrun > /etc/s6-overlay/s6-rc.d/hermes-mcp-http/type; \
    mkdir -p /etc/s6-overlay/s6-rc.d/hermes-mcp-http/dependencies.d; \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-mcp-http; \
    chmod 0755 /etc/s6-overlay/s6-rc.d/hermes-mcp-http/run /opt/mcp-http/server.py; \
    /opt/mcp-http/bin/python -I -c "import mcp_proxy.mcp_server, mcp_proxy.proxy_server"
