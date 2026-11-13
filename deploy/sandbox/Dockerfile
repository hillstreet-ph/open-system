# Isolated execution sandbox for the Hermes agent (Railway service `open-system-sandbox`).
# Hermes runs terminal / file / execute_code calls here over SSH (terminal.backend: ssh) instead of
# inside the Hermes container, so agent commands never see /opt/data or the Hermes secrets.
# Reached only over Railway private networking (open-system-sandbox.railway.internal:2222); no public
# domain. Key-only SSH for one unprivileged user; host key and authorized key come from service
# variables, so redeploys keep the same identity. Workspace persists on the volume at /data.
FROM nikolaik/python-nodejs:python3.12-nodejs22-bookworm

RUN set -eu; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      openssh-server git curl wget jq ripgrep unzip zip less vim-tiny procps build-essential \
      ca-certificates tini; \
    rm -rf /var/lib/apt/lists/* /etc/ssh/ssh_host_*; \
    userdel -r pn 2>/dev/null || true; \
    useradd --uid 1000 --create-home --home-dir /data/home --shell /bin/bash agent; \
    mkdir -p /run/sshd /etc/ssh/authorized_keys

COPY sshd_config /etc/ssh/sshd_config
COPY --chmod=0755 entrypoint.sh /usr/local/bin/sandbox-entrypoint

EXPOSE 2222
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/sandbox-entrypoint"]
