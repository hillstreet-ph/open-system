#!/usr/bin/env python3
"""Boot-time repair of config.yaml files that no longer parse (cont-init 016-config-repair).

Hermes falls back to DEFAULT settings while a config.yaml does not parse (model routing, MCP
servers, plugins and gateway settings are all lost; the gateway reports ``startup_failed``), and
it deliberately refuses every API write over a broken file (``require_readable_config_before_write``),
so the dashboard cannot fix it either. Production hit this on 2026-11-12: stray, mis-indented
``key: value`` lines appended by an agent edit (line 2824, "mapping values are not allowed here").

For the default home and every profile, this script:
1. leaves a file alone when it parses (the normal case: no write, no output beyond one line),
2. otherwise copies it to ``<home>/backups/config/config.yaml.unparseable-<UTC>`` first,
3. drops only the lines the parser rejects (at most 25; never writes if it still fails),
4. writes the result atomically with the original owner and mode.

Key names of dropped lines are logged; values never are. Never fails the boot (exit 0).
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml

HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
MAX_DROPS = 25


def log(msg: str) -> None:
    print(f"[config-repair] {msg}", flush=True)


def repaired_text(text: str) -> tuple[str | None, list[str]]:
    """(new text or None when it already parses, dropped line descriptions)."""
    lines, dropped = text.splitlines(), []
    for _ in range(MAX_DROPS + 1):
        try:
            doc = yaml.safe_load("\n".join(lines) + "\n")
        except yaml.YAMLError as exc:
            mark = getattr(exc, "problem_mark", None)
            if mark is None or not (0 <= mark.line < len(lines)) or len(dropped) >= MAX_DROPS:
                raise RuntimeError(f"cannot repair automatically ({getattr(exc, 'problem', exc)})") from exc
            bad = lines.pop(mark.line)
            dropped.append(f"line {mark.line + len(dropped) + 1}: {bad.split(':', 1)[0].strip() or '<blank>'}")
            continue
        if not dropped:
            return None, []
        if not isinstance(doc, dict):
            raise RuntimeError("repaired document is not a mapping; not writing")
        return "\n".join(lines) + "\n", dropped
    raise RuntimeError("unreachable")


def repair(path: Path) -> None:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        log(f"{path}: unreadable ({exc.__class__.__name__}); skipped")
        return
    try:
        new, dropped = repaired_text(text)
    except RuntimeError as exc:
        log(f"{path}: does NOT parse and {exc}")
        return
    if new is None:
        return
    st = path.stat()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_dir = path.parent / "backups" / "config"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"config.yaml.unparseable-{stamp}"
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
    log(f"{path}: repaired, removed {len(dropped)} line(s) {dropped}; original kept at {backup}")


def main() -> int:
    targets = [HOME / "config.yaml", *sorted((HOME / "profiles").glob("*/config.yaml"))]
    for path in targets:
        if path.is_file():
            try:
                repair(path)
            except Exception as exc:  # never block the boot
                log(f"{path}: repair failed ({exc.__class__.__name__}: {exc})")
    log(f"checked {sum(p.is_file() for p in targets)} config file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
