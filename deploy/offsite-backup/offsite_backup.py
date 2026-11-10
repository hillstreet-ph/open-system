#!/usr/bin/env python3
"""Encrypted off-site backup of the Hermes home to Supabase (open-system-backup-ingest).

Runs as the s6 longrun ``hermes-offsite-backup``. Every OFFSITE_BACKUP_INTERVAL_HOURS (default 6) it:

1. creates a consistent full archive with the official ``hermes backup`` (SQLite copied through the
   backup API, caches/venvs/browser profiles excluded),
2. splits it into Fernet-encrypted parts (``fernet-chunks-v1``, key HERMES_BACKUP_ENCRYPTION_KEY,
   the key registered with the ingest function and used by scripts/recovery-bootstrap.py),
3. uploads each part through the ingest function (HERMES_BACKUP_TRANSFER_TOKEN) and has the server
   verify its SHA-256 and size,
4. uploads and verifies the manifest, which catalogs the backup as FULL_ENCRYPTED_PARTS_VERIFIED,
5. deletes the local archive.

Replaces the agent-driven cron job ``open-system-backup``, which stopped on 2026-11-07 (``Skill
'terminal' not found`` / ``cron fire ownership was lost``). Dormant without both secrets. Never
prints secret values. ``--once`` runs a single backup and exits (used by tests and ad-hoc runs).
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = os.environ.get(
    "OFFSITE_BACKUP_ENDPOINT",
    "https://huadtiuuoiriqrjpjxhr.supabase.co/functions/v1/open-system-backup-ingest")
HERMES = os.environ.get("HERMES_BIN", "/opt/hermes/.venv/bin/hermes")
HOME = Path(os.environ.get("HERMES_HOME", "/opt/data"))
WORK = HOME / "backups" / "offsite"
PLAIN_CHUNK = 6 * 1024 * 1024  # Fernet adds ~34 %; the ingest function caps a part at 9 MiB
RETRIES = 5


def log(msg: str) -> None:
    print(f"[offsite-backup] {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ} {msg}", flush=True)


def env_secret(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        try:
            for line in (HOME / ".env").read_text().splitlines():
                if line.startswith(name + "="):
                    value = line.split("=", 1)[1].strip().strip("'\"")
        except OSError:
            pass
    return value


def request(method: str, params: dict, token: str, body: bytes | None = None) -> tuple[int, bytes]:
    url = ENDPOINT + "?" + urllib.parse.urlencode(params)
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "open-system-offsite-backup/1"}
    if body is not None:
        headers["Content-Type"] = "application/octet-stream"
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(url, body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as err:
            if err.code < 500 and err.code != 429:
                return err.code, b""
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(min(60, 5 * attempt))
    return 0, b""


def put_verified(object_name: str, data: bytes, token: str) -> None:
    status, _ = request("PUT", {"object": object_name}, token, data)
    if status not in (200, 201):
        raise RuntimeError(f"upload {object_name.rsplit('/', 1)[1]} failed (HTTP {status})")
    status, raw = request("POST", {"action": "verify", "object": object_name}, token)
    if status != 200:
        raise RuntimeError(f"verify {object_name.rsplit('/', 1)[1]} failed (HTTP {status})")
    reply = json.loads(raw or b"{}")
    if reply.get("sha256") != hashlib.sha256(data).hexdigest() or reply.get("bytes") != len(data):
        raise RuntimeError(f"server checksum mismatch for {object_name.rsplit('/', 1)[1]}")


def make_archive() -> tuple[Path, datetime]:
    WORK.mkdir(parents=True, exist_ok=True)
    for old in WORK.glob("hermes-backup-*.zip"):
        old.unlink(missing_ok=True)  # leftovers of an interrupted run
    snapshot_at = datetime.now(timezone.utc).replace(microsecond=0)
    out = WORK / f"hermes-backup-{snapshot_at:%Y%m%dT%H%M%SZ}-offsite.zip"
    rc = subprocess.run([HERMES, "backup", "-o", str(out), "-k", "0"], env={**os.environ, "HERMES_HOME": str(HOME)},
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False)
    tail = " | ".join(rc.stdout.strip().splitlines()[-3:])
    # exit 1 = archive written but some files were skipped (kept, like the daily backup did)
    if rc.returncode not in (0, 1) or not out.is_file():
        raise RuntimeError(f"hermes backup exited {rc.returncode}: {tail}")
    log(f"archive {out.name} {out.stat().st_size / 1e9:.2f} GB ({tail})")
    return out, snapshot_at


def upload(archive: Path, snapshot_at: datetime, token: str, key: str) -> str:
    from cryptography.fernet import Fernet  # shipped in the Hermes venv

    fernet = Fernet(key.encode())
    prefix = f"v1/{snapshot_at:%Y%m%dT%H%M%S}-{secrets.token_hex(4).upper()}"
    parts, whole = [], hashlib.sha256()
    with archive.open("rb") as fh:
        index = 0
        while chunk := fh.read(PLAIN_CHUNK):
            whole.update(chunk)
            index += 1
            name = f"part-{index:05d}.enc"
            token_bytes = fernet.encrypt(chunk)
            put_verified(f"{prefix}/{name}", token_bytes, token)
            parts.append({"name": name, "sha256": hashlib.sha256(token_bytes).hexdigest(), "bytes": len(token_bytes)})
            if index % 50 == 0:
                log(f"{prefix}: {index} parts uploaded")
    manifest = {
        "version": 1, "cipher": "fernet-chunks-v1", "kind": "full", "parts": parts,
        "archive_bytes": archive.stat().st_size, "archive_sha256": whole.hexdigest(),
        "source_snapshot_at": snapshot_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "hermes backup (open-system offsite service)",
    }
    put_verified(f"{prefix}/manifest.json", json.dumps(manifest).encode(), token)
    return prefix


def run_once() -> bool:
    token, key = env_secret("HERMES_BACKUP_TRANSFER_TOKEN"), env_secret("HERMES_BACKUP_ENCRYPTION_KEY")
    if not token or len(key) != 44:
        log("dormant: HERMES_BACKUP_TRANSFER_TOKEN / HERMES_BACKUP_ENCRYPTION_KEY not set")
        return False
    archive = None
    try:
        archive, snapshot_at = make_archive()
        prefix = upload(archive, snapshot_at, token, key)
        log(f"OK {prefix} verified ({archive.stat().st_size / 1e9:.2f} GB)")
        (WORK / "last-success").write_text(f"{prefix} {snapshot_at:%Y-%m-%dT%H:%M:%SZ}\n")
        return True
    except Exception as exc:  # keep the service alive; the next interval retries
        log(f"FAILED: {exc}")
        return False
    finally:
        if archive is not None:
            archive.unlink(missing_ok=True)


def main() -> None:
    if "--once" in sys.argv:
        sys.exit(0 if run_once() else 1)
    interval = max(1.0, float(os.environ.get("OFFSITE_BACKUP_INTERVAL_HOURS", "6"))) * 3600
    time.sleep(float(os.environ.get("OFFSITE_BACKUP_START_DELAY_SECONDS", "900")))  # let the gateway settle
    while True:
        started = time.monotonic()
        run_once()
        time.sleep(max(300.0, interval - (time.monotonic() - started)))


if __name__ == "__main__":
    main()
