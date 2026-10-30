FROM hillstreet/open-system@sha256:7d7620db45e9dce4c2a25a1f3bbd864531d9320391f4902090dbaf690e08fc25 AS legacy
FROM nousresearch/hermes-agent@sha256:9c5561579f3ffdf333401797094ac3a743738d6c25d40f4331c7bf77b694238d

# Retain the existing Open-System tunnel while upgrading Hermes itself.
COPY --from=legacy /usr/local/bin/tunnel-client /usr/local/bin/tunnel-client
COPY --from=legacy /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel
COPY --from=legacy /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-mcp-tunnel /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-mcp-tunnel

# The Hermes MCP server moved from core into this official plugin in v0.22.
ARG PLUGIN_COMMIT=6389dd08c1e485db708688c69e42c2b7a7360f4e
RUN set -eu; \
    mkdir -p /opt/hermes/plugins/mcp-serve /opt/hermes/plugins/spotify /opt/hermes/plugins/langfuse; \
    curl -fsSL --retry 3 "https://github.com/NousResearch/hermes-official-plugins/archive/${PLUGIN_COMMIT}.tar.gz" -o /tmp/mcp-plugin.tar.gz; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/mcp-serve "hermes-official-plugins-${PLUGIN_COMMIT}/mcp-serve"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/spotify "hermes-official-plugins-${PLUGIN_COMMIT}/spotify"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/langfuse "hermes-official-plugins-${PLUGIN_COMMIT}/langfuse"; \
    /opt/hermes/.venv/bin/python -m ensurepip; \
    /opt/hermes/.venv/bin/python -m pip install --no-cache-dir "langfuse==4.15.2"; \
    rm /tmp/mcp-plugin.tar.gz; \
    sed -i 's/hermes mcp serve/hermes mcp-serve/' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run; \
    test -f /opt/hermes/plugins/mcp-serve/plugin.yaml; \
    test -f /opt/hermes/plugins/spotify/plugin.yaml; \
    test -f /opt/hermes/plugins/langfuse/plugin.yaml; \
    grep -q 'hermes mcp-serve' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run
