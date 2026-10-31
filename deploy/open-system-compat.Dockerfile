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
    echo '34db1de3f19de74fd0ae59abc7976a339ea171c70fa9ce39e06296a89d520da2  /tmp/mcp-plugin.tar.gz' | sha256sum -c -; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/mcp-serve "hermes-official-plugins-${PLUGIN_COMMIT}/mcp-serve"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/spotify "hermes-official-plugins-${PLUGIN_COMMIT}/spotify"; \
    tar -xzf /tmp/mcp-plugin.tar.gz --strip-components=2 -C /opt/hermes/plugins/langfuse "hermes-official-plugins-${PLUGIN_COMMIT}/langfuse"; \
    /opt/hermes/.venv/bin/python -m ensurepip; \
    printf '%s\n' \
      'langfuse==4.15.2 --hash=sha256:98c27a3c06e18c4497045f2d4decce2c716ef11cb215cf5b27bbea6ee0877115' \
      'backoff==2.2.1 --hash=sha256:63579f9a0628e06278f7e47b7d7d5b6ce20dc65c5e96a6f3ca99a6adca0396e8' \
      'wrapt==2.5.2 --hash=sha256:59b7e6d1dea7c3f38bab21954f587499c27c16ea537058eee4add6e4da1780ea' > /tmp/compat-requirements.txt; \
    /opt/hermes/.venv/bin/python -m pip install --no-cache-dir --no-deps --require-hashes -r /tmp/compat-requirements.txt; \
    rm /tmp/compat-requirements.txt; \
    rm /tmp/mcp-plugin.tar.gz; \
    sed -i 's/hermes mcp serve/hermes mcp-serve/' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run; \
    test -f /opt/hermes/plugins/mcp-serve/plugin.yaml; \
    test -f /opt/hermes/plugins/spotify/plugin.yaml; \
    test -f /opt/hermes/plugins/langfuse/plugin.yaml; \
    grep -q 'hermes mcp-serve' /etc/s6-overlay/s6-rc.d/hermes-mcp-tunnel/run
