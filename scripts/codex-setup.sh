#!/usr/bin/env bash
# Repository-root independent, locked development dependency installation.
set -euo pipefail
project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"
mode="${1:---check}"
case "$mode" in
  --install)
    command -v uv >/dev/null || { echo 'uv is required; install from the official Astral distribution.' >&2; exit 1; }
    uv sync --locked --extra dev
    ;;
  --check) ;;
  *) echo 'Usage: scripts/codex-setup.sh [--check|--install]' >&2; exit 2 ;;
esac
python_bin="$project_root/.venv/bin/python"
[[ -x "$python_bin" ]] || { echo 'Missing .venv. Run scripts/codex-setup.sh --install.' >&2; exit 1; }
"$python_bin" -c 'import sys; assert (3, 11) <= sys.version_info[:2] < (3, 14); import pytest, yaml, openai; from hermes_cli import kanban_db; print("Python and core development imports OK")'
"$python_bin" -m hermes_cli.portfolio
# This script never initializes credentials, starts a dispatcher, or promotes tasks.
