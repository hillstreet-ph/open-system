#!/bin/sh
# Install the host key and the Hermes public key from service variables, then run sshd.
set -eu
: "${SANDBOX_HOST_KEY:?SANDBOX_HOST_KEY (ed25519 private host key) is not set}"
: "${SANDBOX_AUTHORIZED_KEYS:?SANDBOX_AUTHORIZED_KEYS (Hermes public key) is not set}"
umask 077
printf '%s\n' "$SANDBOX_HOST_KEY" > /etc/ssh/ssh_host_ed25519_key
ssh-keygen -y -f /etc/ssh/ssh_host_ed25519_key > /etc/ssh/ssh_host_ed25519_key.pub
umask 022
printf '%s\n' "$SANDBOX_AUTHORIZED_KEYS" > /etc/ssh/authorized_keys/agent
chmod 0644 /etc/ssh/authorized_keys/agent /etc/ssh/ssh_host_ed25519_key.pub
unset SANDBOX_HOST_KEY SANDBOX_AUTHORIZED_KEYS
# Persistent workspace on the volume (first boot creates it).
mkdir -p /data/home/workspace
chown agent:agent /data/home /data/home/workspace
[ -f /data/home/.bashrc ] || { cp /etc/skel/.bashrc /etc/skel/.profile /data/home/ 2>/dev/null || true; chown agent:agent /data/home/.bashrc /data/home/.profile 2>/dev/null || true; }
/usr/sbin/sshd -t
echo "sandbox: sshd listening on :2222 for user agent"
exec /usr/sbin/sshd -D -e
