#!/usr/bin/env python3
"""Move the gadget platform off port 8765 (cont-init 018-gadget-port).

Production hit a permanent port collision on 2026-11-11: the authenticated MCP HTTP bridge
(``hermes-mcp-http``, deploy/mcp-http/) owns 8765 because Railway routes
``mcp.open-system.space`` to it, and the community ``gadget`` platform plugin also defaults to
8765. The gadget therefore never bound, retried forever, and ``/api/status`` reported
``overall: degraded`` with ``gadget_listen_failed`` / ``[Errno 98] address already in use``.

The gadget's port is configurable (``extra.port``, see the plugin's adapter.py), so this script
moves it to ``GADGET_PORT`` (default 8766) for the default home and every profile.

The edit is LINE-BASED on purpose: a production config.yaml carries comments, ordering and
hand-tuned formatting that a YAML round-trip would destroy. Only the gadget block's ``port``
value is rewritten; every other byte is preserved.

1. leaves a file alone when no gadget block exists or the port is already elsewhere,
2. copies it to ``<home>/backups/config/config.yaml.gadget-port-<UTC>`` before writing,
3. writes the result atomically with the original owner and mode.

Never fails the boot (exit 0).
"""
from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
# 8765 is the MCP HTTP bridge (mcp.open-system.space). 8766 is free in the production container
# (api_server 8642, webhook 8644, dashboard 9119).
TARGET_PORT = int(os.environ.get("GADGET_PORT", "8766"))
CONFLICT_PORT = 8765

GADGET_KEY = re.compile(r"^(?P<indent>[ \t]*)gadget:[ \t]*(?:#.*)?$")
PORT_KEY = re.compile(r"^(?P<indent>[ \t]*)port:[ \t]*(?P<value>[^#\n]*?)[ \t]*(?P<comment>#.*)?$")


def log(msg: str) -> None:
    print(f"[gadget-port] {msg}", flush=True)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" \t"))


def _block_end(lines: list[str], start: int, indent: int) -> int:
    """Index one past the last line belonging to the block opened at *start*."""
    i = start + 1
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if _indent(line) <= indent:
            break
        i += 1
    return i


def _port_in_block(lines: list[str], start: int, end: int) -> int | None:
    """Index of the ``port:`` line inside the gadget block, or None."""
    for i in range(start + 1, end):
        if PORT_KEY.match(lines[i]):
            return i
    return None


def rewrite(text: str) -> tuple[str | None, str]:
    """(new text or None when nothing to do, human-readable note)."""
    lines = text.splitlines()
    changed = 0
    notes: list[str] = []
    # Walk backwards so inserting a line never shifts an index we still have to visit.
    for start in range(len(lines) - 1, -1, -1):
        m = GADGET_KEY.match(lines[start])
        if not m:
            continue
        indent = len(m.group("indent"))
        end = _block_end(lines, start, indent)
        port_at = _port_in_block(lines, start, end)
        if port_at is not None:
            pm = PORT_KEY.match(lines[port_at])
            raw = (pm.group("value") or "").strip().strip("'\"")
            try:
                current = int(raw)
            except ValueError:
                current = None
            if current is not None and current != CONFLICT_PORT:
                continue  # already moved (or deliberately set elsewhere)
            comment = pm.group("comment")
            lines[port_at] = (
                f"{pm.group('indent')}port: {TARGET_PORT}" + (f"  {comment}" if comment else "")
            )
            notes.append(f"port {current if current is not None else raw!r} -> {TARGET_PORT}")
            changed += 1
        else:
            # No port key: add one as the block's first child. PlatformConfig.from_dict folds
            # non-typed keys into ``extra``, which is where the adapter reads it.
            lines.insert(start + 1, f"{' ' * (indent + 2)}port: {TARGET_PORT}")
            notes.append(f"port unset -> {TARGET_PORT} (added)")
            changed += 1
    if not changed:
        return None, ""
    return "\n".join(lines) + "\n", "; ".join(notes)


def fix(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        log(f"{path}: unreadable ({exc.__class__.__name__}); skipped")
        return
    try:
        new, note = rewrite(text)
    except Exception as exc:  # never block the boot
        log(f"{path}: rewrite failed ({exc.__class__.__name__}: {exc})")
        return
    if new is None:
        return
    st = path.stat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = path.parent / "backups" / "config"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"config.yaml.gadget-port-{stamp}"
    shutil.copy2(path, backup)
    fd, tmp = tempfile.mkstemp(prefix=".config.yaml.", dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(new)
    os.chmod(tmp, st.st_mode & 0o7777)
    try:
        os.chown(tmp, st.st_uid, st.st_gid)
        os.chown(backup, st.st_uid, st.st_gid)
        os.chown(backup_dir, st.st_uid, st.st_gid)
    except PermissionError:
        pass
    os.replace(tmp, path)
    log(f"{path}: gadget {note}; original kept at {backup}")


def main() -> int:
    targets = [HOME / "config.yaml", *sorted((HOME / "profiles").glob("*/config.yaml"))]
    for path in targets:
        if path.is_file():
            fix(path)
    log(f"checked {sum(p.is_file() for p in targets)} config file(s); gadget target port {TARGET_PORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
