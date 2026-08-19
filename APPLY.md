# Apply Open-System ops pack to GitHub

The GitHub connector for this session does **not** have write permission on
`hillstreet-ph/open-system` (403). Apply these files with an account that can push.

## Option A — Copy into a local clone

```bash
git clone https://github.com/hillstreet-ph/open-system.git
cd open-system
cp -a /path/to/open-system-ops/.github/workflows/* .github/workflows/
cp -a /path/to/open-system-ops/scripts/* scripts/
mkdir -p deploy/zeabur deploy/docker docs
cp -a /path/to/open-system-ops/deploy/* deploy/
cp -a /path/to/open-system-ops/docs/* docs/
# Merge env contract into .env.example (append section)
cat OPEN_SYSTEM_ENV_CONTRACT.env.example >> .env.example
chmod +x scripts/*.sh
git add -A
git commit -m "feat(ops): Open-System CI/CD, Docker Hub release, upstream-sync, ops scripts"
git push origin main
```

## Option B — Grant the connector write access

Reconnect the GitHub integration with **Contents: Read and write** and
**Actions: Read and write** (or admin) on the `hillstreet-ph` organization /
`open-system` repository, then ask to re-run the push.

## After push

1. Confirm secrets exist under **Settings → Secrets and variables → Actions**:
   - `DOCKERHUB_USERNAME`
   - `DOCKERHUB_TOKEN`
2. Optional variable: `DOCKERHUB_IMAGE` = `youruser/open-system`
3. Actions → **Open-System Docker Release** → Run workflow (or push to main).
4. Actions → **Upstream Sync (Hermes)** → Run workflow to open the first sync PR.
5. When an image digest is published, point Zeabur `hermes-agent-v2` at that image
   (do not remove the old `hermes-agent` service).

## Zeabur

Service variables already configured on V2 — no need to paste secrets into git.
Keep volume mount `/opt/data`. Leave ENTRYPOINT/CMD empty (image default).
