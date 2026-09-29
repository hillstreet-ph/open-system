#!/usr/bin/env bash
set -euo pipefail

target="${1:-}"
root="${2:-}"
source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
case "$target" in
  chatgpt|codex) default_root="${CODEX_HOME:-$HOME/.codex}/skills" ;;
  claude) default_root="$HOME/.claude/skills" ;;
  open-connect) default_root="./.agents/skills" ;;
  generic|grok) default_root="./agent-skills" ;;
  *) echo "Usage: $0 {chatgpt|codex|claude|open-connect|grok|generic} [install-root]" >&2; exit 2 ;;
esac
dest_root="${root:-$default_root}"
dest="$dest_root/fullstack-platform-operations"
mkdir -p "$dest_root"
[[ ! -e "$dest" ]] || { echo "Destination already exists: $dest" >&2; exit 3; }
cp -R "$source_dir" "$dest"
echo "Installed instructions at: $dest"
echo "Authorize provider connectors and credentials separately in the target agent."
