# hermes-version: v0.23.1  (base = nousresearch/hermes-agent:v0.22.6, digest-pinned below)
FROM hillstreet/open-system@sha256:7d7620db45e9dce4c2a25a1f3bbd864531d9320391f4902090dbaf690e08fc25 AS legacy
FROM nousresearch/hermes-agent@sha256:276d44685c65c0cb2a25f190b63c65c8906f9dc76486fb1c05ae71b5826bda08

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

# More official plugins (NousResearch/hermes-official-plugins), pinned to the commits the Hermes
# plugin catalog lists (plugin-catalog/hermes-memory-wiki.yaml, hermes-security.yaml). Bundled in the
# image so they survive redeploys; Python/UI only, no long-running processes.
RUN set -eu; \
    fetch() { d="$(mktemp -d)"; git -C "$d" init -q; \
      git -C "$d" fetch -q --depth 1 https://github.com/NousResearch/hermes-official-plugins "$1"; \
      git -C "$d" checkout -q FETCH_HEAD; test "$(git -C "$d" rev-parse HEAD)" = "$1"; \
      cp -a "$d/$2" "/opt/hermes/plugins/$3"; rm -rf "$d"; }; \
    fetch 54afaf5014db23346148436c4883eb64095e8060 memory-wiki memory-wiki; \
    fetch 65f5ad93c7dc14dc661ff2ff3ead0fda71e7bd9d hermes-security hermes-security; \
    rm -rf /opt/hermes/plugins/memory-wiki/tests /opt/hermes/plugins/hermes-security/tests /opt/hermes/plugins/hermes-security/evals; \
    test -f /opt/hermes/plugins/memory-wiki/plugin.yaml; \
    test -f /opt/hermes/plugins/hermes-security/plugin.yaml

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

# Boot-time repair of config.yaml files that no longer parse (Hermes otherwise runs on defaults and
# refuses API writes over the broken file). Runs after 015-supervise-perms, before profile reconcile.
COPY --chmod=0755 deploy/config-repair/016-config-repair /etc/cont-init.d/016-config-repair
COPY deploy/config-repair/requirements.lock deploy/config-repair/config_repair.py /opt/config-repair/
RUN set -eu; \
    "$(readlink -f /opt/hermes/.venv/bin/python3)" -m venv /opt/config-repair/venv; \
    /opt/config-repair/venv/bin/pip install --no-cache-dir --require-hashes --only-binary=:all: -r /opt/config-repair/requirements.lock; \
    chmod 0755 /opt/config-repair/config_repair.py; \
    /opt/config-repair/venv/bin/python -I -c "import yaml"; \
    /opt/config-repair/venv/bin/python -I -m py_compile /opt/config-repair/config_repair.py

# SSH identity for the execution sandbox (deploy/sandbox): agent terminal/file/code calls run in the
# separate Railway service open-system-sandbox over SSH (terminal.backend: ssh). No-op without the key.
COPY --chmod=0755 deploy/sandbox-ssh/017-sandbox-ssh /etc/cont-init.d/017-sandbox-ssh

# Encrypted off-site backup service (Supabase open-system-backup-ingest), replacing the agent cron job.
COPY deploy/offsite-backup/offsite_backup.py /opt/offsite-backup/offsite_backup.py
COPY deploy/offsite-backup/run /etc/s6-overlay/s6-rc.d/hermes-offsite-backup/run
RUN set -eu; \
    echo longrun > /etc/s6-overlay/s6-rc.d/hermes-offsite-backup/type; \
    mkdir -p /etc/s6-overlay/s6-rc.d/hermes-offsite-backup/dependencies.d; \
    touch /etc/s6-overlay/s6-rc.d/user/contents.d/hermes-offsite-backup; \
    chmod 0755 /etc/s6-overlay/s6-rc.d/hermes-offsite-backup/run /opt/offsite-backup/offsite_backup.py; \
    /opt/hermes/.venv/bin/python -I -c "import cryptography.fernet" && /opt/hermes/.venv/bin/python -I -m py_compile /opt/offsite-backup/offsite_backup.py
